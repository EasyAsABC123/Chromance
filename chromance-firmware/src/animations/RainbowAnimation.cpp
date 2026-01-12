#include "RainbowAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"

void RainbowAnimation::run()
{
    // Use update() to set the initial state immediately
    update();
}

void RainbowAnimation::update()
{
    // Use time-based hue calculation to ensure the rainbow animation
    // appears continuous even when switching between animations.
    // Original speed: 1024 units per ~33ms => ~31 units/ms.
    // 32 units/ms gives a ~2 second cycle (65536 / 32 = 2048ms).
    firstHue = (millis() % 2048) * 32;

    // Serial.println("Rainbow hue: " + String(firstHue));
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
