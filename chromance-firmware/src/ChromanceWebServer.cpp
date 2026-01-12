#include "ChromanceWebServer.h"
#include "Constants.h"
#include "animations/Animation.h"
#include "WebAssets.h"
#include "Topology.h"

ChromanceWebServer::ChromanceWebServer(AnimationController &animationController)
    : server(80), ws("/ws"), animationController(animationController)
{
}

void ChromanceWebServer::begin()
{
    setupRoutes();
    server.begin();

    // Register callback for animation changes
    animationController.setStateChangeCallback([this](byte anim, bool autoSwitch)
                                               { this->broadcastStatus(); });
}

void ChromanceWebServer::setupRoutes()
{
    // WebSocket
    ws.onEvent([this](AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len)
               { this->onEvent(server, client, type, arg, data, len); });
    server.addHandler(&ws);

    // Serve Static HTML
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request)
              { request->send(200, "text/html", index_html); });

    server.on("/style.css", HTTP_GET, [](AsyncWebServerRequest *request)
              { request->send(200, "text/css", style_css); });

    server.on("/script.js", HTTP_GET, [](AsyncWebServerRequest *request)
              { request->send(200, "application/javascript", script_js); });

    // API Status
    server.on("/api/status", HTTP_GET, [this](AsyncWebServerRequest *request)
              {
        AsyncResponseStream *response = request->beginResponseStream("application/json");
        response->print(getStatusJson());
        request->send(response); });

    // API Set Animation
    server.on("/api/animation", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total)
              {
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
        } });

    // API Set AutoSwitch
    server.on("/api/autoswitch", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total)
              {
        JsonDocument doc;
        deserializeJson(doc, data);

        if (doc["enabled"].is<bool>()) {
            bool enabled = doc["enabled"];
            animationController.setAutoSwitching(enabled);
            request->send(200, "application/json", "{\"status\":\"ok\"}");
            this->broadcastStatus();
        } else {
            request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Missing enabled\"}");
        } });

    // API Set Sleep
    server.on("/api/sleep", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total)
              {
        JsonDocument doc;
        deserializeJson(doc, data);

        if (doc["enabled"].is<bool>()) {
            bool enabled = doc["enabled"];
            setSleepEnabled(enabled);
            request->send(200, "application/json", "{\"status\":\"ok\"}");
            this->broadcastStatus();
        } else {
            request->send(400, "application/json", "{\"status\":\"error\", \"message\":\"Missing enabled\"}");
        } });

    // API Get Config
    server.on("/api/config", HTTP_GET, [this](AsyncWebServerRequest *request)
              {
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
        } });

    // API Set Config
    server.on("/api/config", HTTP_POST, [](AsyncWebServerRequest *request) {}, NULL, [this](AsyncWebServerRequest *request, uint8_t *data, size_t len, size_t index, size_t total)
              {
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
        } });
}

void ChromanceWebServer::onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len)
{
    if (type == WS_EVT_CONNECT)
    {
        Serial.printf("WebSocket client #%u connected from %s\n", client->id(), client->remoteIP().toString().c_str());

        // Send configuration first
        client->text(getEmulatorConfigJson());

        // Then send status
        client->text(getStatusJson());

        // Default to enabled for backward compatibility
        emulatorClients.push_back(client->id());
        clientsNeedingFullFrame.insert(client->id());
    }
    else if (type == WS_EVT_DISCONNECT)
    {
        Serial.printf("WebSocket client #%u disconnected\n", client->id());
        auto it = std::find(emulatorClients.begin(), emulatorClients.end(), client->id());
        if (it != emulatorClients.end())
        {
            emulatorClients.erase(it);
        }
        clientsNeedingFullFrame.erase(client->id());
    }
    else if (type == WS_EVT_DATA)
    {
        handleWebSocketMessage(client, arg, data, len);
    }
}

void ChromanceWebServer::handleWebSocketMessage(AsyncWebSocketClient *client, void *arg, uint8_t *data, size_t len)
{
    AwsFrameInfo *info = (AwsFrameInfo *)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT)
    {
        data[len] = 0;
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, (char *)data);
        if (error)
        {
            return;
        }

        if (doc["type"] == "ping")
        {
            client->text("{\"type\":\"pong\"}");
            return;
        }

        if (doc["emulator"].is<bool>())
        {
            bool enabled = doc["emulator"];
            auto it = std::find(emulatorClients.begin(), emulatorClients.end(), client->id());
            if (enabled)
            {
                if (it == emulatorClients.end())
                {
                    emulatorClients.push_back(client->id());
                    clientsNeedingFullFrame.insert(client->id());
                }
            }
            else
            {
                if (it != emulatorClients.end())
                {
                    emulatorClients.erase(it);
                }
            }
        }
    }
}

void ChromanceWebServer::broadcastStatus()
{
    ws.textAll(getStatusJson());
}

void ChromanceWebServer::broadcastLedData()
{
    if (ws.count() == 0 || emulatorClients.empty())
        return;

    // Throttle to ~30fps
    static unsigned long lastUpdate = 0;
    if (millis() - lastUpdate < 33)
        return;
    lastUpdate = millis();

    size_t bufferSize = Constants::NUMBER_OF_SEGMENTS * Constants::LEDS_PER_SEGMENT * 3;
    LedController &led = animationController.getLedController();
    uint8_t *currentData = &led.ledColors[0][0][0];

    // Initialize lastLedData if empty
    if (lastLedData.empty())
    {
        lastLedData.resize(bufferSize, 0);
    }

    // Calculate Diff
    // Format: [Type(1), Count(2), [Index(2), R, G, B]...]
    std::vector<uint8_t> diffPayload;
    diffPayload.push_back(1); // Type 1 = Diff
    diffPayload.push_back(0); // Count High placeholder
    diffPayload.push_back(0); // Count Low placeholder

    uint16_t changeCount = 0;
    // Iterate pixels
    for (size_t i = 0; i < bufferSize / 3; i++)
    {
        size_t idx = i * 3;
        if (currentData[idx] != lastLedData[idx] ||
            currentData[idx + 1] != lastLedData[idx + 1] ||
            currentData[idx + 2] != lastLedData[idx + 2])
        {
            changeCount++;
            // Index (2 bytes)
            diffPayload.push_back((i >> 8) & 0xFF);
            diffPayload.push_back(i & 0xFF);
            // RGB
            diffPayload.push_back(currentData[idx]);
            diffPayload.push_back(currentData[idx + 1]);
            diffPayload.push_back(currentData[idx + 2]);
        }
    }

    // Update count in payload
    diffPayload[1] = (changeCount >> 8) & 0xFF;
    diffPayload[2] = changeCount & 0xFF;

    // Determine if we should send Full or Diff
    // Full payload size: 1 (Type) + bufferSize
    // Diff payload size: diffPayload.size()
    bool preferFull = (diffPayload.size() > (bufferSize + 1));

    // Prepare Full Payload if needed
    // We construct it on demand to avoid memory usage if not needed,
    // or we could use a static buffer.
    // Let's just create a vector for it if we need it.
    std::vector<uint8_t> fullPayload;
    if (preferFull || !clientsNeedingFullFrame.empty())
    {
        fullPayload.reserve(bufferSize + 1);
        fullPayload.push_back(0); // Type 0 = Full
        fullPayload.insert(fullPayload.end(), currentData, currentData + bufferSize);
    }

    for (uint32_t id : emulatorClients)
    {
        bool needsFull = clientsNeedingFullFrame.count(id) > 0;

        if (needsFull || preferFull)
        {
            ws.binary(id, fullPayload.data(), fullPayload.size());
            if (needsFull)
            {
                clientsNeedingFullFrame.erase(id);
            }
        }
        else
        {
            ws.binary(id, diffPayload.data(), diffPayload.size());
        }
    }

    // Update lastLedData
    memcpy(lastLedData.data(), currentData, bufferSize);
}

String ChromanceWebServer::getStatusJson()
{
    JsonDocument doc;
    doc["type"] = "status";
    doc["currentAnimation"] = animationController.getCurrentAnimation();
    doc["autoSwitching"] = animationController.isAutoSwitching();
    doc["sleepEnabled"] = sleepEnabled;

    JsonArray anims = doc["animations"].to<JsonArray>();
    for (int i = 0; i < Constants::NUMBER_OF_ANIMATIONS; i++)
    {
        Animation *anim = animationController.getAnimation(i);
        if (anim != nullptr)
        {
            JsonObject animObj = anims.add<JsonObject>();
            animObj["id"] = i;
            animObj["name"] = anim->getName();
        }
    }

    String jsonString;
    serializeJson(doc, jsonString);
    return jsonString;
}

String ChromanceWebServer::getEmulatorConfigJson()
{
    JsonDocument doc;
    doc["type"] = "config";
    doc["ledsPerSegment"] = Constants::LEDS_PER_SEGMENT;

    JsonArray nodes = doc["nodePositions"].to<JsonArray>();
    for (int i = 0; i < Constants::NUMBER_OF_NODES; i++)
    {
        JsonObject n = nodes.add<JsonObject>();
        n["x"] = Topology::nodePositions[i].x;
        n["y"] = Topology::nodePositions[i].y;
    }

    JsonArray segs = doc["segmentConnections"].to<JsonArray>();
    for (int i = 0; i < Constants::NUMBER_OF_SEGMENTS; i++)
    {
        JsonArray s = segs.add<JsonArray>();
        s.add(Topology::segmentConnections[i][0]);
        s.add(Topology::segmentConnections[i][1]);
    }

    String jsonString;
    serializeJson(doc, jsonString);
    return jsonString;
}
