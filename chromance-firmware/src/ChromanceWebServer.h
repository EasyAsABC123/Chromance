#ifndef CHROMANCE_WEB_SERVER_H
#define CHROMANCE_WEB_SERVER_H

#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>
#include "AnimationController.h"

class ChromanceWebServer
{
public:
    ChromanceWebServer(AnimationController &animationController);
    void begin();

private:
    AsyncWebServer server;
    AnimationController &animationController;

    void setupRoutes();
};

#endif
