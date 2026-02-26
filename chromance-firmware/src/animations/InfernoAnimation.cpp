#include "InfernoAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"
#include <cmath>

InfernoAnimation::InfernoAnimation(AnimationController &controller) : Animation(controller), finished(true)
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
    startTime = millis();
    duration = Constants::ANIMATION_TIME * 3; // Make it last longer than standard
    finished = false;
}

bool InfernoAnimation::canBePreempted()
{
    return finished;
}

bool InfernoAnimation::isFinished()
{
    return finished;
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
    if (finished) return;

    // Check if we should stop adding fuel (time up)
    bool fuelEnabled = (millis() - startTime < duration);
    
    // 1. Cooling
    float maxHeat = 0.0f;
    for (int i = 0; i < Constants::NUM_OF_PIXELS; i++)
    {
        // Slightly more cooling to help the bottom go dark
        heatPixels[i] -= (random(15) / 1000.0f) + 0.005f;
        if (heatPixels[i] < 0.0f)
            heatPixels[i] = 0.0f;
        
        if (heatPixels[i] > maxHeat) maxHeat = heatPixels[i];
    }
    
    // Check finish condition: No fuel left and heat is low
    if (!fuelEnabled && maxHeat < 0.05f) {
        finished = true;
        // Clear leds
        controller.getLedController().clear();
        return;
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
            // Reduced the current pixel's retention (0.01) to make it more of a 'rising' fireball
            nextHeat[currentIdx] = (heatPixels[currentIdx] * 0.01f) + (heatPixels[belowIdx] * 0.98f);
            
            // As heat moves up, the source below loses heat (cooling effect of moving fuel)
            nextHeat[belowIdx] *= 0.95f; 
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
                    nextHeat[currentIdx] = (heatPixels[currentIdx] * 0.01f) + (heatPixels[sourceIdx] * 0.98f);
                    nextHeat[sourceIdx] *= 0.95f;
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
    if (fuelEnabled) {
        for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
        {
            int n0 = Topology::segmentConnections[s][0];
            int n1 = Topology::segmentConnections[s][1];

            // Only ignite the very bottom segments
            if (Topology::nodePositions[n0].y >= 22 || Topology::nodePositions[n1].y >= 22)
            {
                // Less frequent bursts to allow the previous fire to rise as a plume/ball
                if (random(100) < 10)
                {
                    // Ignite bottom LED
                    int idx = s * Constants::LEDS_PER_SEGMENT + 0;
                    heatPixels[idx] += (random(80, 150) / 100.0f);

                    if (heatPixels[idx] > 1.0f)
                        heatPixels[idx] = 1.0f;
                }
            }
        }
    }

    // 4. Render
    LedController &lc = controller.getLedController();
    lc.clear(); // Important to clear for non-additive rendering or handle black yourself
    
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
        // else black (already cleared)
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(InfernoAnimation)
