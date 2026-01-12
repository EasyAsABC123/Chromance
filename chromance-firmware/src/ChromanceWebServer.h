#ifndef CHROMANCE_WEB_SERVER_H
#define CHROMANCE_WEB_SERVER_H

#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include <set>
#include "AnimationController.h"

class ChromanceWebServer
{
public:
    ChromanceWebServer(AnimationController &animationController);
    void begin();
    bool isSleepEnabled() const { return sleepEnabled; }
    void broadcastLedData();

private:
    AsyncWebServer server;
    AsyncWebSocket ws;
    AnimationController &animationController;
    std::vector<uint32_t> emulatorClients;
    std::set<uint32_t> clientsNeedingFullFrame;
    std::vector<uint8_t> lastLedData;
    bool sleepEnabled = false;

    void setupRoutes();
    void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len);
    void handleWebSocketMessage(AsyncWebSocketClient *client, void *arg, uint8_t *data, size_t len);
    void broadcastStatus();
    String getStatusJson();
    String getEmulatorConfigJson();
    void setSleepEnabled(bool enabled) { sleepEnabled = enabled; }

    // Friend function or access to LedController if needed, but animationController has it.
};

#endif
