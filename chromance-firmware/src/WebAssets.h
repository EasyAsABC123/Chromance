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
  // Emulator Data
  const nodePositions = [
    {x:20,y:1}, {x:40,y:1}, {x:60,y:1},
    {x:10,y:4}, {x:30,y:4}, {x:50,y:4}, {x:70,y:4},
    {x:20,y:7}, {x:40,y:7}, {x:60,y:7},
    {x:10,y:10}, {x:30,y:10}, {x:50,y:10}, {x:70,y:10},
    {x:20,y:13}, {x:40,y:13}, {x:60,y:13},
    {x:30,y:16}, {x:50,y:16},
    {x:20,y:19}, {x:40,y:19}, {x:60,y:19},
    {x:30,y:22}, {x:50,y:22},
    {x:40,y:25}
  ];
  const segmentConnections = [
    [0,3], [0,4], [1,4], [1,5], [2,5], [2,6],
    [3,7], [4,7], [4,8], [5,8], [5,9], [6,9],
    [3,10], [7,14], [4,11], [8,15], [5,12], [9,16], [6,13],
    [10,14], [11,14], [11,15], [12,15], [12,16], [13,16],
    [14,17], [15,17], [15,18], [16,18],
    [14,19], [17,22], [15,20], [18,23], [16,21],
    [19,22], [20,22], [20,23], [21,23],
    [22,24], [23,24]
  ];
  const LEDS_PER_SEGMENT = 14;
  const SCALE_X = 10;
  const SCALE_Y = 10;

  let currentConfig = {};
  var gateway = `ws://${window.location.hostname}/ws`;
  var websocket;
  const canvas = document.getElementById('emulatorCanvas');
  const ctx = canvas.getContext('2d');
  let emulatorEnabled = true;
  // Initialize buffer for 40 segments * 14 LEDs * 3 channels = 1680 bytes
  const TOTAL_LEDS = 40 * 14;
  const LED_BUFFER_SIZE = TOTAL_LEDS * 3;
  let ledState = new Uint8Array(LED_BUFFER_SIZE);

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
    // Send initial emulator state
    emulatorEnabled = document.getElementById('emulatorToggle').checked;
    websocket.send(JSON.stringify({emulator: emulatorEnabled}));
  }

  function onClose(event) {
    console.log('Connection closed');
    setTimeout(initWebSocket, 2000);
  }

  function onMessage(event) {
    if (event.data instanceof ArrayBuffer) {
        if (emulatorEnabled) {
            handleBinaryData(new Uint8Array(event.data));
        }
    } else {
        var data = JSON.parse(event.data);
        updateUI(data);
    }
  }

  function handleBinaryData(data) {
      if (data.length === 0) return;

      const type = data[0];

      if (type === 0) { // Full Frame
          // data[1...] is the led data
          // Copy to local state
          if (data.length - 1 === LED_BUFFER_SIZE) {
              ledState.set(data.subarray(1));
          } else {
              console.warn("Received full frame with incorrect size", data.length);
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
      if (emulatorEnabled) drawGrid();
  }

  function drawGrid() {
      // Clear with background
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw faint lines for segments
      ctx.strokeStyle = '#222';
      ctx.lineWidth = 2;
      segmentConnections.forEach(seg => {
          const p1 = nodePositions[seg[0]];
          const p2 = nodePositions[seg[1]];
          ctx.beginPath();
          ctx.moveTo(canvas.width - (p1.x * SCALE_X), p1.y * SCALE_Y);
          ctx.lineTo(canvas.width - (p2.x * SCALE_X), p2.y * SCALE_Y);
          ctx.stroke();
      });
  }

  function drawLeds(data) {
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
            const r = data[baseIdx];
            const g = data[baseIdx+1];
            const b = data[baseIdx+2];

            // Interpolate position
            const t = i / (LEDS_PER_SEGMENT - 1);
            // Note: implementation in test_main.cpp used pB + (pA - pB) * t which means it starts at B?
            // Let's stick to standard interpolation p1 + (p2 - p1) * t
            // But check orientation if it matters for effects (e.g. chases).
            // test_main.cpp: pB + (pA - pB) * t -> t=0 is pB (Node 2), t=1 is pA (Node 1)
            // This implies Segment Connections are defined as {NodeA, NodeB} but mapped backwards?
            // Let's just try p1->p2 first.
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
    document.getElementById('autoSwitch').checked = data.autoSwitching;
    const select = document.getElementById('animationSelect');
    const currentAnim = data.currentAnimation;

    if (select.options.length <= 1) {
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

  function toggleAutoSwitch() {
    const enabled = document.getElementById('autoSwitch').checked;
    fetch('/api/autoswitch', {
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
)js";

#endif
