#include "RainbowAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"

void RainbowAnimation::run()
{
    firstHue = 0;
    controller.getLedController().rainbow(firstHue, brightness);
}

void RainbowAnimation::update()
{
    firstHue += 1024;
    controller.getLedController().rainbow(firstHue, brightness);
}

void RainbowAnimation::getConfig(JsonObject &doc)
{
    doc["brightness"] = brightness;
}

void RainbowAnimation::setConfig(const JsonObject &doc)
{
    if (doc["brightness"].is<int>())
    {
        brightness = doc["brightness"];
    }
}
