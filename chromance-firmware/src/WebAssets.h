#ifndef WEB_ASSETS_H
#define WEB_ASSETS_H

#include <Arduino.h>

const char index_html[] PROGMEM = R"html(
<!DOCTYPE HTML><html>
<head>
  <title>Chromance Control</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
  <div class="card">
    <h1>Chromance</h1>

    <div class="toggle-container">
      <span>Auto Switching</span>
      <label class="switch">
        <input type="checkbox" id="autoSwitch" onchange="toggleAutoSwitch()">
        <span class="slider"></span>
      </label>
    </div>

    <div class="toggle-container">
      <span>Allow Deep Sleep</span>
      <label class="switch">
        <input type="checkbox" id="sleepToggle" onchange="toggleSleep()">
        <span class="slider"></span>
      </label>
    </div>

    <div class="toggle-container">
      <span>Show Emulator</span>
      <label class="switch">
        <input type="checkbox" id="emulatorToggle" onchange="toggleEmulator()" checked>
        <span class="slider"></span>
      </label>
    </div>

    <label for="animationSelect">Select Animation:</label>
    <select id="animationSelect" onchange="changeAnimation()">
      <option value="" disabled selected>Loading...</option>
    </select>

    <div id="configSection" style="display:none; border-top: 1px solid #555; margin-top: 20px; padding-top: 20px;">
        <h3>Configuration</h3>
        <div id="configFields"></div>
        <button onclick="saveConfig()">Save Configuration</button>
    </div>

    <canvas id="emulatorCanvas" width="800" height="260"></canvas>

    <div id="status" style="margin-top: 20px; font-size: 12px; color: #888;"></div>
  </div>

<script src="script.js"></script>
</body>
</html>
)html";

const char style_css[] PROGMEM = R"css(
body { font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 20px; background-color: #222; color: #fff; }
h1 { color: #00bcd4; }
.card { background-color: #333; max-width: 800px; margin: 0 auto; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
select, button, input[type=text], input[type=number] { padding: 10px; margin: 10px 0; width: 100%; font-size: 16px; border-radius: 5px; border: none; box-sizing: border-box; }
select, input[type=text], input[type=number] { background-color: #444; color: #fff; }
button { background-color: #00bcd4; color: white; cursor: pointer; font-weight: bold; }
button:hover { background-color: #008ba3; }
.toggle-container { display: flex; align-items: center; justify-content: space-between; margin: 15px 0; }
.switch { position: relative; display: inline-block; width: 60px; height: 34px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; -webkit-transition: .4s; transition: .4s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; -webkit-transition: .4s; transition: .4s; border-radius: 50%; }
input:checked + .slider { background-color: #2196F3; }
input:focus + .slider { box-shadow: 0 0 1px #2196F3; }
input:checked + .slider:before { -webkit-transform: translateX(26px); -ms-transform: translateX(26px); transform: translateX(26px); }
.config-field { margin: 10px 0; text-align: left; }
.config-field label { display: block; margin-bottom: 5px; color: #aaa; }
canvas { background: #000; border-radius: 5px; margin-top: 20px; width: 100%; max-width: 600px; aspect-ratio: 80/26; }
)css";

const char script_js[] PROGMEM = R"js(
  // Emulator Data - Initialized from WebSocket config
  let nodePositions = [];
  let segmentConnections = [];
  let LEDS_PER_SEGMENT = 14; // Default, will be updated
  const SCALE_X = 10;
  const SCALE_Y = 10;

  let currentConfig = {};
  var gateway = `ws://${window.location.hostname}/ws`;
  var websocket;
  const canvas = document.getElementById('emulatorCanvas');
  const ctx = canvas.getContext('2d');
  let emulatorEnabled = true;
  // Initialize buffer size dynamically if possible, or large enough
  // Defaulting to max size for now until config is received
  let TOTAL_LEDS = 40 * 14;
  let LED_BUFFER_SIZE = TOTAL_LEDS * 3;
  let ledState = new Uint8Array(LED_BUFFER_SIZE);

  let heartbeatInterval;
  let connectionTimeout;

  window.addEventListener('load', onLoad);

  function onLoad(event) {
    initWebSocket();
    // Initialize toggle state
    emulatorEnabled = document.getElementById('emulatorToggle').checked;
    toggleEmulator(); // Apply state
  }

  function initWebSocket() {
    console.log('Trying to open a WebSocket connection...');
    websocket = new WebSocket(gateway);
    websocket.binaryType = "arraybuffer";
    websocket.onopen    = onOpen;
    websocket.onclose   = onClose;
    websocket.onmessage = onMessage;
  }

  function onOpen(event) {
    console.log('Connection opened');
    startHeartbeat();
    // Send initial emulator state
    emulatorEnabled = document.getElementById('emulatorToggle').checked;
    websocket.send(JSON.stringify({emulator: emulatorEnabled}));
  }

  function onClose(event) {
    console.log('Connection closed');
    stopHeartbeat();
    setTimeout(initWebSocket, 2000);
  }

  function onMessage(event) {
    resetConnectionTimeout();
    if (event.data instanceof ArrayBuffer) {
        if (emulatorEnabled) {
            handleBinaryData(new Uint8Array(event.data));
        }
    } else {
        var data = JSON.parse(event.data);
        if (data.type === 'config') {
            nodePositions = data.nodePositions;
            segmentConnections = data.segmentConnections;
            LEDS_PER_SEGMENT = data.ledsPerSegment;

            // Re-init buffer if needed
            TOTAL_LEDS = segmentConnections.length * LEDS_PER_SEGMENT;
            LED_BUFFER_SIZE = TOTAL_LEDS * 3;
            // Only resize if significantly different or if we want to be safe
            if (ledState.length < LED_BUFFER_SIZE) {
                ledState = new Uint8Array(LED_BUFFER_SIZE);
            }

            drawGrid();
            console.log("Config received", data);
        } else if (data.type === 'status' || !data.type) {
            updateUI(data);
        }
    }
  }

  function handleBinaryData(data) {
      if (data.length === 0) return;

      const type = data[0];

      if (type === 0) { // Full Frame
          // data[1...] is the led data
          // Copy to local state
          if (data.length - 1 <= LED_BUFFER_SIZE) {
              ledState.set(data.subarray(1));
          } else {
              // If buffer is too small, just copy what we can
               ledState.set(data.subarray(1, LED_BUFFER_SIZE + 1));
          }
      } else if (type === 1) { // Diff Frame
          // Structure: [Type(1), CountHigh(1), CountLow(1), (IndexHigh, IndexLow, R, G, B)...]
          if (data.length < 3) return;

          const count = (data[1] << 8) | data[2];
          let ptr = 3;

          for (let i = 0; i < count; i++) {
              if (ptr + 4 >= data.length) break;

              const idx = (data[ptr] << 8) | data[ptr+1];
              const r = data[ptr+2];
              const g = data[ptr+3];
              const b = data[ptr+4];

              const byteIdx = idx * 3;
              if (byteIdx + 2 < LED_BUFFER_SIZE) {
                  ledState[byteIdx] = r;
                  ledState[byteIdx+1] = g;
                  ledState[byteIdx+2] = b;
              }

              ptr += 5;
          }
      }

      drawLeds(ledState);
  }

  function toggleEmulator() {
      emulatorEnabled = document.getElementById('emulatorToggle').checked;
      if (websocket && websocket.readyState === WebSocket.OPEN) {
          websocket.send(JSON.stringify({emulator: emulatorEnabled}));
      }
      const canvas = document.getElementById('emulatorCanvas');
      canvas.style.display = emulatorEnabled ? 'block' : 'none';
      if (emulatorEnabled && nodePositions.length > 0) drawGrid();
  }

  function drawGrid() {
      if (!nodePositions.length || !segmentConnections.length) return;

      // Clear with background
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw faint lines for segments
      ctx.strokeStyle = '#222';
      ctx.lineWidth = 2;
      segmentConnections.forEach(seg => {
          if (seg[0] < nodePositions.length && seg[1] < nodePositions.length) {
              const p1 = nodePositions[seg[0]];
              const p2 = nodePositions[seg[1]];
              ctx.beginPath();
              ctx.moveTo(canvas.width - (p1.x * SCALE_X), p1.y * SCALE_Y);
              ctx.lineTo(canvas.width - (p2.x * SCALE_X), p2.y * SCALE_Y);
              ctx.stroke();
          }
      });
  }

  function drawLeds(data) {
      if (!nodePositions.length || !segmentConnections.length) return;

      // Redraw grid first to clear previous frame and show connections
      drawGrid();

      // Data is Flat: [Seg0Led0R, Seg0Led0G, Seg0Led0B, Seg0Led1R, ...]
      for (let s = 0; s < segmentConnections.length; s++) {
        const seg = segmentConnections[s];
        // In Topology.cpp, segmentConnections is [CeilingNode, FloorNode].
        // LedController maps index 0 to the Floor index, so we must draw from Floor to Ceiling.
        const p1 = nodePositions[seg[1]]; // Floor (Start)
        const p2 = nodePositions[seg[0]]; // Ceiling (End)

        for (let i = 0; i < LEDS_PER_SEGMENT; i++) {
            const baseIdx = (s * LEDS_PER_SEGMENT * 3) + (i * 3);
            if (baseIdx + 2 >= data.length) continue;

            const r = data[baseIdx];
            const g = data[baseIdx+1];
            const b = data[baseIdx+2];

            // Interpolate position
            const t = i / (LEDS_PER_SEGMENT - 1);
            const x = p1.x + (p2.x - p1.x) * t;
            const y = p1.y + (p2.y - p1.y) * t;

            if (r > 5 || g > 5 || b > 5) {
                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.beginPath();
                ctx.arc(canvas.width - (x * SCALE_X), y * SCALE_Y, 3, 0, 2 * Math.PI);
                ctx.fill();
            } else {
                // Dim dot for unlit
                ctx.fillStyle = '#111';
                ctx.beginPath();
                ctx.arc(canvas.width - (x * SCALE_X), y * SCALE_Y, 1, 0, 2 * Math.PI);
                ctx.fill();
            }
        }
      }
  }

  function updateUI(data) {
    if (data.autoSwitching !== undefined) {
        document.getElementById('autoSwitch').checked = data.autoSwitching;
    }
    if (data.sleepEnabled !== undefined) {
      document.getElementById('sleepToggle').checked = data.sleepEnabled;
    }
    const select = document.getElementById('animationSelect');
    if (data.currentAnimation !== undefined) {
        const currentAnim = data.currentAnimation;

        if (select.options.length <= 1 && data.animations) {
            select.innerHTML = '';
            data.animations.forEach(anim => {
                const option = document.createElement('option');
                option.value = anim.id;
                option.text = anim.name;
                select.appendChild(option);
            });
        }

        if (select.value != currentAnim && document.activeElement !== select) {
             select.value = currentAnim;
             fetchConfig(currentAnim);
        }
    }
  }

  function toggleAutoSwitch() {
    const enabled = document.getElementById('autoSwitch').checked;
    fetch('/api/autoswitch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: enabled })
    });
  }

  function toggleSleep() {
    const enabled = document.getElementById('sleepToggle').checked;
    fetch('/api/sleep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: enabled })
    });
  }

  function changeAnimation() {
    const id = document.getElementById('animationSelect').value;
    fetch('/api/animation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: parseInt(id) })
    })
    .then(() => {
        document.getElementById('autoSwitch').checked = false;
        fetchConfig(id);
    });
  }

  function fetchConfig(id) {
      fetch('/api/config?id=' + id)
      .then(response => response.json())
      .then(data => {
          const container = document.getElementById('configFields');
          const section = document.getElementById('configSection');
          container.innerHTML = '';
          currentConfig = data;

          const keys = Object.keys(data);
          if (keys.length > 0) {
              section.style.display = 'block';
              keys.forEach(key => {
                  const val = data[key];
                  const div = document.createElement('div');
                  div.className = 'config-field';

                  const label = document.createElement('label');
                  label.innerText = key;
                  div.appendChild(label);

                  const input = document.createElement('input');
                  input.id = 'config_' + key;
                  if (typeof val === 'number') {
                      input.type = 'number';
                      input.value = val;
                  } else if (typeof val === 'boolean') {
                      input.type = 'checkbox';
                      input.checked = val;
                  } else {
                      input.type = 'text';
                      input.value = val;
                  }
                  div.appendChild(input);
                  container.appendChild(div);
              });
          } else {
              section.style.display = 'none';
          }
      });
  }

  function saveConfig() {
      const id = document.getElementById('animationSelect').value;
      const newConfig = {};
      Object.keys(currentConfig).forEach(key => {
          const input = document.getElementById('config_' + key);
          if (input.type === 'checkbox') {
              newConfig[key] = input.checked;
          } else if (input.type === 'number') {
              newConfig[key] = parseFloat(input.value);
          } else {
              newConfig[key] = input.value;
          }
      });

      fetch('/api/config?id=' + id, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newConfig)
      }).then(res => {
          if (res.ok) alert('Saved!');
          else alert('Error saving');
      });
  }

  function startHeartbeat() {
      stopHeartbeat();
      // Send ping every 5 seconds
      heartbeatInterval = setInterval(() => {
          if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify({type: 'ping'}));
          }
      }, 5000);
  }

  function stopHeartbeat() {
      if (heartbeatInterval) clearInterval(heartbeatInterval);
      if (connectionTimeout) clearTimeout(connectionTimeout);
  }

  function resetConnectionTimeout() {
      if (connectionTimeout) clearTimeout(connectionTimeout);
      // Wait 10 seconds for a response/data before timing out
      connectionTimeout = setTimeout(() => {
          console.log('Connection timeout, closing WebSocket');
          if (websocket) websocket.close();
      }, 10000);
  }
)js";

#endif
