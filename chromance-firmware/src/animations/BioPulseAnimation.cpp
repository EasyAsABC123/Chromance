#include "BioPulseAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

void BioPulseAnimation::run()
{
}

void BioPulseAnimation::update()
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
        int nodeA = Topology::segmentConnections[s][0];
        int nodeB = Topology::segmentConnections[s][1];
        NodePosition pA = Topology::nodePositions[nodeA];
        NodePosition pB = Topology::nodePositions[nodeB];
        
        float midX = (pA.x + pB.x) / 2.0f;
        float midY = (pA.y + pB.y) / 2.0f;
        
        float dx = midX - center.x;
        float dy = midY - center.y;
        float dist = sqrt(dx*dx + dy*dy);

        // Calculate sine wave
        // sin outputs -1 to 1
        float val = sin(timeSec * speed - dist * phaseFactor);
        
        // Map -1..1 to 0..1
        float brightness = (val + 1.0f) / 2.0f;
        
        // Apply gamma/power for better visual contrast
        brightness = brightness * brightness; // Simple gamma 2.0

        // Scale to 0-255
        uint8_t v = (uint8_t)(brightness * 255);
        
        uint32_t color = leds.ColorHSV(hue, 255, v);
        
        byte r = (byte)((color >> 16) & 0xFF);
        byte g = (byte)((color >> 8) & 0xFF);
        byte b = (byte)(color & 0xFF);

        // Apply to all pixels in segment
        for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
            leds.addPixelColor(s, i, r, g, b);
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(BioPulseAnimation)
