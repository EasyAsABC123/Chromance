#include "InfernoAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

#include "InfernoAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"
#include <cmath>

InfernoAnimation::InfernoAnimation(AnimationController &controller) : Animation(controller)
{
    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
    {
        heatPixels[i] = 0.0f;
    }
}

void InfernoAnimation::run()
{
    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
    {
        heatPixels[i] = 0.0f;
    }
}

uint32_t InfernoAnimation::getHeatColor(float h)
{
    if (h <= 0.0f)
        return 0;
    if (h > 1.0f)
        h = 1.0f;

    uint8_t r = 0, g = 0, b = 0;

    if (h < 0.4f)
    {
        // 0.0 - 0.4: Black to Red
        float val = (h / 0.4f);
        val = val * val; // Quadratic for deeper black
        r = (uint8_t)(val * 255);
        g = 0;
        b = 0;
    }
    else if (h < 0.7f)
    {
        // 0.4 - 0.7: Red to Orange
        r = 255;
        float t = (h - 0.4f) / 0.3f;
        g = (uint8_t)(t * 128); // Green 0 -> 128
        b = 0;
    }
    else
    {
        // 0.7 - 1.0: Orange to Yellow
        r = 255;
        float t = (h - 0.7f) / 0.3f;
        g = 128 + (uint8_t)(t * 127); // Green 128 -> 255
        b = 0;
    }

    return (uint32_t)((r << 16) | (g << 8) | b);
}

void InfernoAnimation::update()
{
    // 1. Cooling
    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
    {
        heatPixels[i] -= (random(30) / 1000.0f) + 0.01f;
        if (heatPixels[i] < 0.0f)
            heatPixels[i] = 0.0f;
    }

    // 2. Convection (Heat rises)
    float nextHeat[Constants::NUM_OF_PIXELS];
    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
        nextHeat[i] = heatPixels[i];

    for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
    {
        // Internal convection (Pixel 0 -> 13)
        // Heat moves UP.
        // Pixel i (higher) gets heat from i-1 (lower).
        for (int i = Constants::LEDS_PER_SEGMENT - 1; i > 0; i--)
        {
            int currentIdx = s * Constants::LEDS_PER_SEGMENT + i;
            int belowIdx = s * Constants::LEDS_PER_SEGMENT + (i - 1);

            // Move heat up (Advection/Diffusion blend)
            // Mostly take from below to move the plume up, sum <= 1.0 to prevent runaway heat
            nextHeat[currentIdx] = (heatPixels[currentIdx] * 0.1f) + (heatPixels[belowIdx] * 0.9f);
        }

        // Bottom LED (0) gets heat from lower segments
        int bottomNode = Topology::segmentConnections[s][1]; // Side 1 is Floor/Bottom

        int currentIdx = s * Constants::LEDS_PER_SEGMENT + 0;

        for (int k = 0; k < Constants::MAX_PATHS_PER_NODE; k++)
        {
            int neighborSeg = Topology::nodeConnections[bottomNode][k];
            if (neighborSeg >= 0 && neighborSeg != s)
            {
                // Check if neighborSeg connects to bottomNode at its Top (Side 0)
                if (Topology::segmentConnections[neighborSeg][0] == bottomNode)
                {
                    // Heat flows from neighbor Top (LED 13) to current Bottom (LED 0)
                    int sourceIdx = neighborSeg * Constants::LEDS_PER_SEGMENT + (Constants::LEDS_PER_SEGMENT - 1);
                    nextHeat[currentIdx] = (heatPixels[currentIdx] * 0.1f) + (heatPixels[sourceIdx] * 0.9f);
                }
            }
        }
    }

    // Clamp

    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
    {

        if (nextHeat[i] > 1.0f)
            nextHeat[i] = 1.0f;

        heatPixels[i] = nextHeat[i];
    }

    // 3. Ignition (Bottom segments)

    for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
    {

        int n0 = Topology::segmentConnections[s][0];

        int n1 = Topology::segmentConnections[s][1];

        if (Topology::nodePositions[n0].y >= 22 || Topology::nodePositions[n1].y >= 22)
        {

            if (random(100) < 3)
            {

                // Ignite bottom LED

                int idx = s * Constants::LEDS_PER_SEGMENT + 0;

                heatPixels[idx] += (random(150) / 100.0f);

                if (heatPixels[idx] > 1.0f)
                    heatPixels[idx] = 1.0f;
            }
        }
    }

    // 4. Render
    LedController &lc = controller.getLedController();
    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
    {
        int s = i / Constants::LEDS_PER_SEGMENT;
        int l = i % Constants::LEDS_PER_SEGMENT;

        uint32_t c = getHeatColor(heatPixels[i]);

        if (c > 0)
        {
            byte r = (c >> 16) & 0xFF;
            byte g = (c >> 8) & 0xFF;
            byte b = c & 0xFF;

            // Flicker
            if (random(10) == 0)
            {
                float flicker = 0.6f + (random(40) / 100.0f);
                lc.setPixelColor(s, l, (byte)(r * flicker), (byte)(g * flicker), (byte)(b * flicker));
            }
            else
            {
                lc.setPixelColor(s, l, r, g, b);
            }
        }
        else
        {
            lc.setPixelColor(s, l, 0, 0, 0);
        }
    }
}
#include "../AnimationRegistry.h"
REGISTER_ANIMATION(InfernoAnimation)