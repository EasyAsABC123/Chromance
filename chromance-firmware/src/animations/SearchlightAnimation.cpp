#include "SearchlightAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

void SearchlightAnimation::run()
{
    // Can reset angle here if desired
    // currentAngle = 0.0f;
}

void SearchlightAnimation::update()
{
    // Rotation speed: radians per frame
    // Assuming update runs ~30-60fps.
    // Full rotation = 2PI.
    // 0.05 rad/frame approx 1 full rotation every ~125 frames (2-4 seconds).
    currentAngle += 0.05f;
    if (currentAngle > M_PI) currentAngle -= 2 * M_PI;

    // Center node position (Node 15)
    // 40, 13
    NodePosition center = Topology::nodePositions[15];
    
    // Beam width in radians
    float beamWidth = 0.4f;

    LedController& leds = controller.getLedController();
    uint32_t color = controller.getRandomColor(); 
    // Or use a fixed radar green: 0x00FF00
    // Let's use baseColor but ensure it's bright
    // uint32_t color = leds.ColorHSV(controller.getBaseColor(), 255, 255);

    // Fade out existing (done globally in AnimationController::update usually, but we can enforce it)
    // Actually, AnimationController calls fade() before update(), so we just draw on top.

    for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
    {
        int nodeA = Topology::segmentConnections[s][0];
        int nodeB = Topology::segmentConnections[s][1];

        NodePosition pA = Topology::nodePositions[nodeA];
        NodePosition pB = Topology::nodePositions[nodeB];

        // Midpoint of segment
        float midX = (pA.x + pB.x) / 2.0f;
        float midY = (pA.y + pB.y) / 2.0f;

        // Vector from center
        float dx = midX - center.x;
        float dy = midY - center.y;

        // Angle of segment relative to center
        float angle = atan2(dy, dx);

        // Normalize angle difference to -PI to +PI
        float diff = angle - currentAngle;
        while (diff <= -M_PI) diff += 2 * M_PI;
        while (diff > M_PI) diff -= 2 * M_PI;

        // Calculate brightness based on proximity to beam center
        if (std::abs(diff) < beamWidth)
        {
            float intensity = 1.0f - (std::abs(diff) / beamWidth);
            // intensity = pow(intensity, 2); // Sharpen beam

            // Draw segment
            // Reduced max brightness (80 instead of 255) to prevent brownout crashes
            uint32_t segColor = leds.ColorHSV(controller.getBaseColor(), 255, 80 * intensity);
            
            byte r = (byte)((segColor >> 16) & 0xFF);
            byte g = (byte)((segColor >> 8) & 0xFF);
            byte b = (byte)(segColor & 0xFF);

            for (int i = 0; i < Constants::LEDS_PER_SEGMENT; i++)
            {
                leds.addPixelColor(s, i, r, g, b);
            }
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(SearchlightAnimation)
