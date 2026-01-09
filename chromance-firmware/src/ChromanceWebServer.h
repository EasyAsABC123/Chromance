#ifndef CHROMANCE_WEB_SERVER_H
#define CHROMANCE_WEB_SERVER_H

#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <vector>
#include <set>
#include <algorithm>
#include "AnimationController.h"

class ChromanceWebServer
{
public:
    ChromanceWebServer(AnimationController &animationController);
    void begin();
    void broadcastStatus();
    void broadcastLedData();

private:
    AsyncWebServer server;
    AsyncWebSocket ws;
    AnimationController &animationController;
    std::vector<uint32_t> emulatorClients;
    std::set<uint32_t> clientsNeedingFullFrame;
    std::vector<uint8_t> lastLedData;

    void setupRoutes();
    void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len);
    void handleWebSocketMessage(AsyncWebSocketClient *client, void *arg, uint8_t *data, size_t len);
    String getStatusJson();
};

#endif
