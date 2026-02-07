#include "PlasmaAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"
#include <cmath>

REGISTER_ANIMATION(PlasmaAnimation)

void PlasmaAnimation::run() {}

void PlasmaAnimation::update()
{
    unsigned long time = millis();
    float time1 = time / 1000.0f;
    float time2 = time / 1234.0f;
    float time3 = time / 2345.0f;

    LedController& leds = controller.getLedController();

    for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
    {
        // Interpolate for each LED
        int nodeTop = Topology::segmentConnections[s][0];
        int nodeBottom = Topology::segmentConnections[s][1];
        NodePosition pTop = Topology::nodePositions[nodeTop];
        NodePosition pBottom = Topology::nodePositions[nodeBottom];

        for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
            float t = (float)i / (Constants::LEDS_PER_SEGMENT - 1);
            float x = pBottom.x + (pTop.x - pBottom.x) * t;
            float y = pBottom.y + (pTop.y - pBottom.y) * t;
            
            // Normalize coords (approx 0-80, 0-26) to 0-1 range
            float u = x / 80.0f;
            float v = y / 26.0f;

            // Calculate plasma value
            float v1 = sin(u * 10.0f + time1);
            float v2 = sin(10.0f * (u * sin(time2) + v * cos(time2)) + time1);
            float cx = u + 0.5f * sin(time3);
            float cy = v + 0.5f * cos(time3);
            float v3 = sin(sqrt(100.0f * (cx*cx + cy*cy)) + time1);
            
            float val = (v1 + v2 + v3) / 3.0f; // -1 to 1
            
            // Map to color
            // Hue based on val
            uint16_t hue = (uint16_t)((val + 1.0f) * 32768.0f);
            
            // Brightness variation
            uint8_t bright = 128 + (uint8_t)(sin(val * 3.14f) * 127);
            
            uint32_t color = leds.ColorHSV(hue, 255, bright);
            
            byte r = (byte)((color >> 16) & 0xFF);
            byte g = (byte)((color >> 8) & 0xFF);
            byte b = (byte)(color & 0xFF);

            leds.setPixelColor(s, i, r, g, b);
        }
    }
}
