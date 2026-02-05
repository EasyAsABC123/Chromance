#include "WaveAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

void WaveAnimation::run()
{
}

void WaveAnimation::update()
{
    unsigned long time = millis();
    float timeSec = time / 1000.0f;
    
    // Pulse parameters
    float speed = 2.0f; // Rad/sec
    float phaseFactor = 0.1f; // Phase shift per unit distance

    NodePosition center = Topology::nodePositions[15];
    LedController& leds = controller.getLedController();

    // Use a fixed or slowly changing hue
    uint16_t hue = (time / 20) % 65536;

    for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
    {
        // Side 0: Ceiling (Top), Side 1: Floor (Bottom)
        int nodeTop = Topology::segmentConnections[s][0];
        int nodeBottom = Topology::segmentConnections[s][1];
        NodePosition pTop = Topology::nodePositions[nodeTop];
        NodePosition pBottom = Topology::nodePositions[nodeBottom];
        
        // Nested loop for each LED in the segment
        for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
            // Calculate interpolation factor (i=0 is bottom, i=max is top)
            float t = (float)i / (Constants::LEDS_PER_SEGMENT - 1);
            
            // Interpolate position
            float ledX = pBottom.x + (pTop.x - pBottom.x) * t;
            float ledY = pBottom.y + (pTop.y - pBottom.y) * t;
            
            float dx = ledX - center.x;
            float dy = ledY - center.y;
            float dist = sqrt(dx*dx + dy*dy);

            // Calculate sine wave based on individual LED distance
            float val = sin(timeSec * speed - dist * phaseFactor);
            
            // Map -1..1 to 0..1
            float brightness = (val + 1.0f) / 2.0f;
            
            // Apply gamma for visual contrast
            brightness = brightness * brightness;

            // Scale to 0-255
            uint8_t v = (uint8_t)(brightness * 255);
            
            uint32_t color = leds.ColorHSV(hue, 255, v);
            
            byte r = (byte)((color >> 16) & 0xFF);
            byte g = (byte)((color >> 8) & 0xFF);
            byte b = (byte)(color & 0xFF);

            leds.setPixelColor(s, i, r, g, b);
        }
    }
}
