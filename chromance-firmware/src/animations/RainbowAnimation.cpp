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
    // moves continuously.
    // Speed: 2048ms for full cycle (65536 hue units)
    firstHue = (millis() % 2048) * 32;

    // Define scale for the spatial gradient
    // Total height is roughly 25 units.
    // 2000 * 25 = 50000, which is close to one full rainbow (65536).
    const float Y_SCALE = 2000.0f;

    for (int i = 0; i < Constants::NUMBER_OF_SEGMENTS; i++)
    {
        // Get connected nodes to determine vertical position
        // Side 0: Closer to ceiling (Top)
        // Side 1: Closer to floor (Bottom)
        int ceilingNode = Topology::segmentConnections[i][0];
        int floorNode = Topology::segmentConnections[i][1];

        float yCeiling = Topology::nodePositions[ceilingNode].y;
        float yFloor = Topology::nodePositions[floorNode].y;

        for (int led = 0; led < Constants::LEDS_PER_SEGMENT; led++)
        {
            // Calculate interpolation factor (0.0 at floor/bottom, 1.0 at ceiling/top)
            float ratio = (float)led / (Constants::LEDS_PER_SEGMENT - 1);

            // Interpolate Y position for this LED
            // led 0 corresponds to floorNode (see LedController::show mapping)
            float currentY = yFloor + (yCeiling - yFloor) * ratio;

            // Calculate hue based on Y position and time offset
            // Adding time-based firstHue makes the pattern move "up"
            // (assuming y=1 is top and we want upward motion)
            uint16_t pixelHue = firstHue + (uint16_t)(currentY * Y_SCALE);

            uint32_t color = controller.getLedController().ColorHSV(pixelHue, 255, brightness);

            // Extract RGB components
            byte r = (uint8_t)(color >> 16);
            byte g = (uint8_t)(color >> 8);
            byte b = (uint8_t)(color);

            controller.getLedController().setPixelColor(i, led, r, g, b);
        }
    }
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
