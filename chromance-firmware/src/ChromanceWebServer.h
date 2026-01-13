#ifndef CHROMANCE_WEB_SERVER_H
#define CHROMANCE_WEB_SERVER_H

#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <vector>
#include <set>
#include "AnimationController.h"
#include "Configuration.h"

class ChromanceWebServer
{
public:
    ChromanceWebServer(AnimationController &animationController, Configuration &configuration);
    void begin();
    void broadcastLedData();

private:
    AsyncWebServer server;
    AsyncWebSocket ws;
    AnimationController &animationController;
    Configuration &configuration;
    std::vector<uint32_t> emulatorClients;
    std::set<uint32_t> clientsNeedingFullFrame;
    std::vector<uint8_t> lastLedData;

    void setupRoutes();
    void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len);
    void handleWebSocketMessage(AsyncWebSocketClient *client, void *arg, uint8_t *data, size_t len);
    void broadcastStatus();
    String getStatusJson();
    String getEmulatorConfigJson();

    // Friend function or access to LedController if needed, but animationController has it.
};

#endif
