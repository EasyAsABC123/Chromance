#include "ChromanceWebServer.h"
#include "Constants.h"
#include "animations/Animation.h"

const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <title>Chromance Control</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 20px; background-color: #222; color: #fff; }
    h1 { color: #00bcd4; }
    .card { background-color: #333; max-width: 400px; margin: 0 auto; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
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
  </style>
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

    <label for="animationSelect">Select Animation:</label>
    <select id="animationSelect" onchange="changeAnimation()">
      <option value="" disabled selected>Loading...</option>
    </select>

    <div id="configSection" style="display:none; border-top: 1px solid #555; margin-top: 20px; padding-top: 20px;">
        <h3>Configuration</h3>
        <div id="configFields"></div>
        <button onclick="saveConfig()">Save Configuration</button>
    </div>

    <div id="status" style="margin-top: 20px; font-size: 12px; color: #888;"></div>
  </div>

<script>
  let currentConfig = {};

  function fetchStatus() {
    fetch('/api/status')
      .then(response => response.json())
      .then(data => {
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
             // Only fetch config if we haven't manually selected another one to edit
             // or just update it.
             fetchConfig(currentAnim);
        }
      })
      .catch(error => console.error('Error:', error));
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

  // Poll status every 5 seconds
  setInterval(fetchStatus, 5000);
  // Initial fetch
  fetchStatus();
</script>
</body>
</html>
)rawliteral";

ChromanceWebServer::ChromanceWebServer(AnimationController &animationController)
    : server(80), animationController(animationController)
{
}

void ChromanceWebServer::begin()
{
    setupRoutes();
    server.begin();
}

void ChromanceWebServer::setupRoutes()
{
    // Serve Static HTML
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
        request->send(200, "text/html", index_html);
    });

    // API Status
    server.on("/api/status", HTTP_GET, [this](AsyncWebServerRequest *request) {
        AsyncResponseStream *response = request->beginResponseStream("application/json");
        JsonDocument doc;

        doc["currentAnimation"] = animationController.getCurrentAnimation();
        doc["autoSwitching"] = animationController.isAutoSwitching();

        JsonArray anims = doc["animations"].to<JsonArray>();
        for (int i = 0; i < Constants::NUMBER_OF_ANIMATIONS; i++) {
            Animation* anim = animationController.getAnimation(i);
            if (anim != nullptr) {
                JsonObject animObj = anims.add<JsonObject>();
                animObj["id"] = i;
                animObj["name"] = anim->getName();
            }
        }

        serializeJson(doc, *response);
        request->send(response);
    });

    // API Set Animation
    server.on("/api/animation", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
        JsonDocument doc;
        deserializeJson(doc, data);

        if (doc["id"].is<int>()) {
            int id = doc["id"];
            // Disable auto switching if manually selecting
            animationController.setAutoSwitching(false);
            animationController.changeAnimation(id);
            request->send(200, "application/json", "{\"status\":\"ok\"}");
        } else {
            request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Missing id\"}");
        }
    });

    // API Set AutoSwitch
    server.on("/api/autoswitch", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
        JsonDocument doc;
        deserializeJson(doc, data);

        if (doc["enabled"].is<bool>()) {
            bool enabled = doc["enabled"];
            animationController.setAutoSwitching(enabled);
            request->send(200, "application/json", "{\"status\":\"ok\"}");
        } else {
            request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Missing enabled\"}");
        }
    });

    // API Get Config
    server.on("/api/config", HTTP_GET, [this](AsyncWebServerRequest *request) {
        if (request->hasParam("id")) {
            int id = request->getParam("id")->value().toInt();
            Animation* anim = animationController.getAnimation(id);
            if (anim) {
                 AsyncResponseStream *response = request->beginResponseStream("application/json");
                 JsonDocument doc;
                 JsonObject obj = doc.to<JsonObject>();
                 anim->getConfig(obj);
                 serializeJson(doc, *response);
                 request->send(response);
            } else {
                request->send(404, "application/json", "{\"status\":\"error\", \"message\":\"Animation not found\"}");
            }
        } else {
             request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Missing id\"}");
        }
    });

    // API Set Config
    server.on("/api/config", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total) {
        if (request->hasParam("id")) {
            int id = request->getParam("id")->value().toInt();
            Animation* anim = animationController.getAnimation(id);
            if (anim) {
                JsonDocument doc;
                deserializeJson(doc, data);
                anim->setConfig(doc.as<JsonObject>());
                request->send(200, "application/json", "{\"status\":\"ok\"}");
            } else {
                 request->send(404, "application/json", "{\"status\":\"error\", \"message\":\"Animation not found\"}");
            }
        } else {
             request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Missing id\"}");
        }
    });
}
