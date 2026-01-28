#include "RainbowPinwheelAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void RainbowPinwheelAnimation::run()
{
    // Use update() to set the initial state immediately
    update();
}

void RainbowPinwheelAnimation::update()
{
    // Calculate center node position
    const NodePosition &centerPos = Topology::nodePositions[Topology::starburstNode];

    // Time-based rotation - similar speed to RainbowAnimation
    // 32 units/ms gives a ~2 second cycle for full rotation
    float rotationOffset = (millis() % 2048) * rotationSpeed * rotationDirection;

    // Calculate angle and apply rainbow for each pixel
    for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; segment++)
    {
        // Get the two nodes connected by this segment
        int node0 = Topology::segmentConnections[segment][0];
        int node1 = Topology::segmentConnections[segment][1];

        // Get node positions
        const NodePosition &pos0 = Topology::nodePositions[node0];
        const NodePosition &pos1 = Topology::nodePositions[node1];

        // Calculate per-pixel colors along the segment
        for (int led = 0; led < Constants::LEDS_PER_SEGMENT; led++)
        {
            // Interpolate position along the segment (0.0 to 1.0)
            float t = (float)led / (Constants::LEDS_PER_SEGMENT - 1);
            float ledX = pos0.x + (pos1.x - pos0.x) * t;
            float ledY = pos0.y + (pos1.y - pos0.y) * t;

            // Calculate angle from center to this LED position
            float dx = ledX - centerPos.x;
            float dy = ledY - centerPos.y;
            float angle = atan2(dy, dx); // Returns angle in radians from -PI to PI

            // Convert angle to hue space (0 to 65536)
            // Normalize angle to 0-2PI, then scale to 0-65536
            float normalizedAngle = angle + M_PI; // Shift from [-PI, PI] to [0, 2PI]
            uint16_t angleHue = (uint16_t)(normalizedAngle * 65536.0f / (2.0f * M_PI));

            // Apply rotation offset and calculate final hue
            uint16_t hue = (angleHue + (uint16_t)rotationOffset) % 65536;

            // Apply rainbow color to this pixel
            uint32_t color = controller.getLedController().ColorHSV(hue, 255, brightness);
            byte r = (uint8_t)(color >> 16);
            byte g = (uint8_t)(color >> 8);
            byte b = (uint8_t)(color);

            controller.getLedController().setPixelColor(segment, led, r, g, b);
        }
    }
}

void RainbowPinwheelAnimation::getConfig(JsonObject &doc)
{
    doc["brightness"] = brightness;
    doc["rotationDirection"] = rotationDirection;
}

void RainbowPinwheelAnimation::setConfig(const JsonObject &doc)
{
    if (doc["brightness"].is<int>())
    {
        brightness = doc["brightness"];
    }
    if (doc["rotationDirection"].is<int>())
    {
        rotationDirection = doc["rotationDirection"];
        if (rotationDirection != 1 && rotationDirection != -1)
        {
            rotationDirection = 1; // Default to clockwise
        }
    }
}
