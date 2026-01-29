#ifndef WEB_ASSETS_H
#define WEB_ASSETS_H

#include <Arduino.h>

const char index_html[] PROGMEM = R"html(
<!DOCTYPE HTML><html>
<head>
  <meta charset="UTF-8">
  <title>Chromance Control</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
  <div class="card">
    <div class="header-container">
        <h1>Chromance</h1>
        <button class="icon-btn" onclick="openGlobalSettings()">⚙️</button>
    </div>

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

    <div class="section">
        <h3>Animations</h3>
        <div id="animationsList">Loading...</div>
    </div>

    <!-- Global Settings Modal -->
    <div id="globalSettingsModal" style="display:none;" class="modal">
        <div class="modal-content">
            <h3>Global Settings</h3>
            <div class="config-field">
                <label>Rainbow Brightness (0-255)</label>
                <input type="number" id="global_rainbowBrightness" min="0" max="255">
            </div>
            <div style="display:flex; gap:10px; margin-top:15px;">
                <button onclick="saveGlobalConfig()">Save</button>
                <button onclick="closeGlobalSettings()" style="background-color:#666">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Animation Config Modal -->
    <div id="animConfigSection" style="display:none;" class="modal">
        <div class="modal-content">
            <h3 id="animConfigTitle">Config</h3>
            <div id="animConfigFields"></div>
            <div style="display:flex; gap:10px; margin-top:15px;">
                <button onclick="saveAnimConfig()">Save</button>
                <button onclick="closeAnimConfig()" style="background-color:#666">Cancel</button>
            </div>
        </div>
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
h1 { color: #00bcd4; margin: 0; }
.card { background-color: #333; max-width: 800px; margin: 0 auto; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
.header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.icon-btn { background: none; border: none; font-size: 24px; cursor: pointer; padding: 5px; margin: 0; width: auto; }
.icon-btn:hover { background: none; opacity: 0.8; }
select, button, input[type=text], input[type=number] { padding: 10px; margin: 5px 0; width: 100%; font-size: 16px; border-radius: 5px; border: none; box-sizing: border-box; }
select, input[type=text], input[type=number] { background-color: #444; color: #fff; }
button { background-color: #00bcd4; color: white; cursor: pointer; font-weight: bold; margin-top: 10px; }
button:hover { background-color: #008ba3; }
.toggle-container { display: flex; align-items: center; justify-content: space-between; margin: 15px 0; }
.switch { position: relative; display: inline-block; width: 60px; height: 34px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; -webkit-transition: .4s; transition: .4s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; -webkit-transition: .4s; transition: .4s; border-radius: 50%; }
input:checked + .slider { background-color: #2196F3; }
input:focus + .slider { box-shadow: 0 0 1px #2196F3; }
input:checked + .slider:before { -webkit-transform: translateX(26px); -ms-transform: translateX(26px); transform: translateX(26px); }
.section { border-top: 1px solid #555; margin-top: 20px; padding-top: 10px; text-align: left; }
.config-field { margin: 10px 0; text-align: left; }
.config-field label { display: block; margin-bottom: 5px; color: #aaa; }
canvas { background: #000; border-radius: 5px; margin-top: 20px; width: 100%; max-width: 600px; aspect-ratio: 80/26; }

.anim-row { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #3a3a3a; margin-bottom: 5px; border-radius: 4px; }
.anim-name { flex-grow: 1; text-align: left; font-weight: bold; }
.anim-controls { display: flex; align-items: center; gap: 8px; }
.btn-small { padding: 6px 12px; font-size: 14px; margin: 0; width: auto; }
.active-indicator { width: 10px; height: 10px; border-radius: 50%; background-color: #444; display: inline-block; margin-right: 10px; }
.active-indicator.active { background-color: #00bcd4; box-shadow: 0 0 5px #00bcd4; }

.modal { position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; }
.modal-content { background-color: #333; margin: auto; padding: 20px; border: 1px solid #888; width: 90%; max-width: 500px; border-radius: 10px; }
)css";

const char script_js[] PROGMEM = R"js(
  let nodePositions = [];
  let segmentConnections = [];
  let LEDS_PER_SEGMENT = 14;
  const SCALE_X = 10;
  const SCALE_Y = 10;

  let currentAnimConfig = {};
  let currentAnimId = -1;

  var gateway = `ws://${window.location.hostname}/ws`;
  var websocket;
  const canvas = document.getElementById('emulatorCanvas');
  const ctx = canvas.getContext('2d');
  let emulatorEnabled = true;
  let TOTAL_LEDS = 40 * 14;
  let LED_BUFFER_SIZE = TOTAL_LEDS * 3;
  let ledState = new Uint8Array(LED_BUFFER_SIZE);

  let heartbeatInterval;
  let connectionTimeout;

  window.addEventListener('load', onLoad);

  function onLoad(event) {
    initWebSocket();
    emulatorEnabled = document.getElementById('emulatorToggle').checked;
    toggleEmulator();
    // Pre-load global config so it's ready when the cog is clicked
    fetchGlobalConfig();
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
            TOTAL_LEDS = segmentConnections.length * LEDS_PER_SEGMENT;
            LED_BUFFER_SIZE = TOTAL_LEDS * 3;
            if (ledState.length < LED_BUFFER_SIZE) {
                ledState = new Uint8Array(LED_BUFFER_SIZE);
            }
            drawGrid();
        } else if (data.type === 'status' || !data.type) {
            updateUI(data);
        }
    }
  }

  function handleBinaryData(data) {
      if (data.length === 0) return;
      const type = data[0];
      if (type === 0) { // Full
          if (data.length - 1 <= LED_BUFFER_SIZE) {
              ledState.set(data.subarray(1));
          } else {
               ledState.set(data.subarray(1, LED_BUFFER_SIZE + 1));
          }
      } else if (type === 1) { // Diff
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
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
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
      drawGrid();
      for (let s = 0; s < segmentConnections.length; s++) {
        const seg = segmentConnections[s];
        const p1 = nodePositions[seg[1]];
        const p2 = nodePositions[seg[0]];
        for (let i = 0; i < LEDS_PER_SEGMENT; i++) {
            const baseIdx = (s * LEDS_PER_SEGMENT * 3) + (i * 3);
            if (baseIdx + 2 >= data.length) continue;
            const r = data[baseIdx];
            const g = data[baseIdx+1];
            const b = data[baseIdx+2];
            const t = i / (LEDS_PER_SEGMENT - 1);
            const x = p1.x + (p2.x - p1.x) * t;
            const y = p1.y + (p2.y - p1.y) * t;
            if (r > 5 || g > 5 || b > 5) {
                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.beginPath();
                ctx.arc(canvas.width - (x * SCALE_X), y * SCALE_Y, 3, 0, 2 * Math.PI);
                ctx.fill();
            } else {
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

    if (data.animations) {
        const list = document.getElementById('animationsList');
        list.innerHTML = '';
        data.animations.forEach(anim => {
            const isActive = data.currentAnimation === anim.id;
            const row = document.createElement('div');
            row.className = 'anim-row';

            const nameDiv = document.createElement('div');
            nameDiv.className = 'anim-name';
            nameDiv.innerHTML = `<span class="active-indicator ${isActive ? 'active' : ''}"></span>${anim.name}`;
            row.appendChild(nameDiv);

            const controls = document.createElement('div');
            controls.className = 'anim-controls';

            // Play Button
            const playBtn = document.createElement('button');
            playBtn.className = 'btn-small';
            playBtn.innerText = 'Play';
            playBtn.onclick = () => playAnimation(anim.id);
            if (isActive) playBtn.style.backgroundColor = '#4CAF50';
            controls.appendChild(playBtn);

            // Enabled Checkbox
            const checkLabel = document.createElement('label');
            checkLabel.style.display = 'flex';
            checkLabel.style.alignItems = 'center';
            checkLabel.style.margin = '0';
            const check = document.createElement('input');
            check.type = 'checkbox';
            check.checked = anim.enabled;
            check.style.width = 'auto';
            check.style.marginRight = '5px';
            check.onchange = (e) => toggleAnimEnabled(anim.id, e.target.checked);
            checkLabel.appendChild(check);
            checkLabel.appendChild(document.createTextNode('Auto'));
            controls.appendChild(checkLabel);

            // Config Button
            const configBtn = document.createElement('button');
            configBtn.className = 'btn-small';
            configBtn.innerText = '⚙';
            configBtn.onclick = () => openAnimConfig(anim.id, anim.name);
            controls.appendChild(configBtn);

            row.appendChild(controls);
            list.appendChild(row);
        });
    }
  }

  function toggleAutoSwitch() {
    fetch('/api/autoswitch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: document.getElementById('autoSwitch').checked })
    });
  }

  function toggleSleep() {
    fetch('/api/sleep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: document.getElementById('sleepToggle').checked })
    });
  }

  function playAnimation(id) {
    fetch('/api/animation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: id })
    });
  }

  function toggleAnimEnabled(id, enabled) {
    fetch('/api/config?id=' + id, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enabled })
    });
  }

  function fetchGlobalConfig() {
      fetch('/api/config/global')
      .then(res => res.json())
      .then(data => {
          if (data.rainbowBrightness !== undefined) {
              document.getElementById('global_rainbowBrightness').value = data.rainbowBrightness;
          }
      });
  }

  function openGlobalSettings() {
      fetchGlobalConfig();
      document.getElementById('globalSettingsModal').style.display = 'flex';
  }

  function closeGlobalSettings() {
      document.getElementById('globalSettingsModal').style.display = 'none';
  }

  function saveGlobalConfig() {
      const config = {
          rainbowBrightness: parseInt(document.getElementById('global_rainbowBrightness').value)
      };
      fetch('/api/config/global', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
      }).then(res => {
          if (res.ok) {
            closeGlobalSettings();
            // alert('Saved Global Settings'); // Optional: remove alert for smoother UX
          }
          else alert('Error saving global settings');
      });
  }

  function openAnimConfig(id, name) {
      currentAnimId = id;
      document.getElementById('animConfigTitle').innerText = 'Config: ' + name;
      document.getElementById('animConfigSection').style.display = 'flex';
      document.getElementById('animConfigFields').innerHTML = 'Loading...';

      fetch('/api/config?id=' + id)
      .then(res => res.json())
      .then(data => {
          currentAnimConfig = data;
          const container = document.getElementById('animConfigFields');
          container.innerHTML = '';
          const keys = Object.keys(data);
          const relevantKeys = keys.filter(k => k !== 'enabled');
          
          if (relevantKeys.length === 0) {
              container.innerHTML = 'No configuration available for this animation.';
          } else {
              relevantKeys.forEach(key => {
                  const val = data[key];
                  const div = document.createElement('div');
                  div.className = 'config-field';
                  const label = document.createElement('label');
                  label.innerText = key;
                  div.appendChild(label);
                  const input = document.createElement('input');
                  input.id = 'cfg_' + key;
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
          }
      });
  }

  function saveAnimConfig() {
      if (currentAnimId === -1) return;
      const newConfig = { ...currentAnimConfig };
      Object.keys(currentAnimConfig).forEach(key => {
          if (key === 'enabled') return; // Don't overwrite enabled from here
          const input = document.getElementById('cfg_' + key);
          if (input) {
            if (input.type === 'checkbox') {
                newConfig[key] = input.checked;
            } else if (input.type === 'number') {
                newConfig[key] = parseFloat(input.value);
            } else {
                newConfig[key] = input.value;
            }
          }
      });

      fetch('/api/config?id=' + currentAnimId, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newConfig)
      }).then(res => {
          if (res.ok) {
              closeAnimConfig();
          } else {
              alert('Error saving');
          }
      });
  }

  function closeAnimConfig() {
      document.getElementById('animConfigSection').style.display = 'none';
  }

  function startHeartbeat() {
      stopHeartbeat();
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
      connectionTimeout = setTimeout(() => {
          console.log('Timeout');
          if (websocket) websocket.close();
      }, 10000);
  }
)js";

#endif
