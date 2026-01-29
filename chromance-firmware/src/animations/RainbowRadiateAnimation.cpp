#include "RainbowRadiateAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <math.h>

void RainbowRadiateAnimation::run()
{
    // Calculate maximum distance from center for normalization
    const NodePosition &centerPos = Topology::nodePositions[Topology::starburstNode];
    maxDistance = 0.0f;

    for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; segment++)
    {
        int node0 = Topology::segmentConnections[segment][0];
        int node1 = Topology::segmentConnections[segment][1];

        const NodePosition &pos0 = Topology::nodePositions[node0];
        const NodePosition &pos1 = Topology::nodePositions[node1];

        float midX = (pos0.x + pos1.x) / 2.0f;
        float midY = (pos0.y + pos1.y) / 2.0f;

        float dx = midX - centerPos.x;
        float dy = midY - centerPos.y;
        float distance = sqrt(dx * dx + dy * dy);

        if (distance > maxDistance)
        {
            maxDistance = distance;
        }
    }

    // Use update() to set the initial state immediately
    update();
}

void RainbowRadiateAnimation::update()
{
    // Calculate center node position
    const NodePosition &centerPos = Topology::nodePositions[Topology::starburstNode];

    // Time-based phase for radiating animation
    // Creates a wave that radiates outward over time
    // 32 units/ms gives a ~2 second cycle
    float phaseOffset = (millis() % 2048) * radiateSpeed;

    // Calculate distance and apply rainbow for each segment
    for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; segment++)
    {
        // Get the two nodes connected by this segment
        int node0 = Topology::segmentConnections[segment][0];
        int node1 = Topology::segmentConnections[segment][1];

        // Get node positions
        const NodePosition &pos0 = Topology::nodePositions[node0];
        const NodePosition &pos1 = Topology::nodePositions[node1];

        for (int led = 0; led < Constants::LEDS_PER_SEGMENT; led++)
        {
            // Interpolate position along the segment (0.0 to 1.0)
            float t = (float)led / (Constants::LEDS_PER_SEGMENT - 1);
            float ledX = pos0.x + (pos1.x - pos0.x) * t;
            float ledY = pos0.y + (pos1.y - pos0.y) * t;

            // Calculate distance from center to this LED
            float dx = ledX - centerPos.x;
            float dy = ledY - centerPos.y;
            float distance = sqrt(dx * dx + dy * dy);

            // Normalize distance (0.0 to 1.0) and add phase offset for animation
            // This creates a wave that radiates outward
            float normalizedDistance = maxDistance > 0 ? (distance / maxDistance) : 0.0f;

            // Map distance + phase to hue space
            float hueValue = (normalizedDistance * 65536.0f + phaseOffset);
            uint16_t hue = (uint16_t)hueValue % 65536;

            // Apply rainbow color to this pixel
            uint32_t color = controller.getLedController().ColorHSV(hue, 255, controller.getConfiguration().getRainbowBrightness());
            byte r = (uint8_t)(color >> 16);
            byte g = (uint8_t)(color >> 8);
            byte b = (uint8_t)(color);

            controller.getLedController().setPixelColor(segment, led, r, g, b);
        }
    }
}
