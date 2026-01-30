#include "InfernoAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

InfernoAnimation::InfernoAnimation(AnimationController &controller) : Animation(controller)
{
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        heat[i] = 0.0f;
    }
}

void InfernoAnimation::run()
{
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        heat[i] = 0.0f;
    }
}

uint32_t InfernoAnimation::getHeatColor(float h)
{
    if (h <= 0.0f) return 0;
    if (h > 1.0f) h = 1.0f;
    
    uint8_t r = 0, g = 0, b = 0;
    
    // Adjusted mapping to favor Red and Orange/Gold
    if (h < 0.5f) {
        // 0.0 - 0.5: Black to Bright Red
        r = (uint8_t)((h / 0.5f) * 255);
        g = 0;
        b = 0;
    } else if (h < 0.85f) {
        // 0.5 - 0.85: Red to Orange/Gold
        // We cap Green at 160 here to stay in the Orange-Gold spectrum longer
        r = 255;
        float localH = (h - 0.5f) / 0.35f; 
        g = (uint8_t)(localH * 160); 
        b = 0;
    } else {
        // 0.85 - 1.0: Gold to White
        r = 255;
        float localH = (h - 0.85f) / 0.15f;
        g = 160 + (uint8_t)(localH * 95); // G goes 160 -> 255
        b = (uint8_t)(localH * 255);      // B goes 0 -> 255
    }
    
    return (uint32_t)((r << 16) | (g << 8) | b);
}

void InfernoAnimation::update()
{
    // 1. Cooling (Slower than before)
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        heat[i] -= (random(5) / 1000.0f) + 0.002f; 
        if(heat[i] < 0.0f) heat[i] = 0.0f;
    }

    // 2. Convection (Upward drift - slightly slower and more filtered)
    float nextHeat[Constants::NUMBER_OF_SEGMENTS];
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) nextHeat[i] = heat[i];

    for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
    {
        int n0 = Topology::segmentConnections[s][0];
        int n1 = Topology::segmentConnections[s][1];
        
        int topNode = (Topology::nodePositions[n0].y < Topology::nodePositions[n1].y) ? n0 : n1;
        int bottomNode = (topNode == n0) ? n1 : n0;

        for (int k = 0; k < Constants::MAX_PATHS_PER_NODE; k++)
        {
            int neighborSeg = Topology::nodeConnections[bottomNode][k];
            if (neighborSeg >= 0 && neighborSeg != s)
            {
                int neighborOther = (Topology::segmentConnections[neighborSeg][0] == bottomNode) 
                                    ? Topology::segmentConnections[neighborSeg][1] 
                                    : Topology::segmentConnections[neighborSeg][0];
                
                if (Topology::nodePositions[neighborOther].y > Topology::nodePositions[bottomNode].y)
                {
                    // Reduced transfer coefficient for slower "rising" fire
                    nextHeat[s] += heat[neighborSeg] * 0.08f; 
                }
            }
        }
        
        if (nextHeat[s] > 1.0f) nextHeat[s] = 1.0f;
    }
    
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) heat[i] = nextHeat[i];

    // 3. Ignition (Bottom segments)
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        int n0 = Topology::segmentConnections[i][0];
        int n1 = Topology::segmentConnections[i][1];
        if (Topology::nodePositions[n0].y >= 22 || Topology::nodePositions[n1].y >= 22) {
             if (random(100) < 10) { // Slightly lower ignition frequency
                 heat[i] += (random(100) / 250.0f); 
                 if (heat[i] > 1.0f) heat[i] = 1.0f;
             }
        }
    }

    // 4. Render
    LedController& lc = controller.getLedController();
    for(int s=0; s<Constants::NUMBER_OF_SEGMENTS; s++) {
        uint32_t c = getHeatColor(heat[s]);
        byte r = (c >> 16) & 0xFF;
        byte g = (c >> 8) & 0xFF;
        byte b = c & 0xFF;
        
        for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
             // Added more organic flickering
             if (random(15) == 0) {
                 float flicker = 0.7f + (random(30) / 100.0f); // 0.7 - 1.0
                 lc.addPixelColor(s, i, (byte)(r * flicker), (byte)(g * flicker), (byte)(b * flicker));
             } else {
                 lc.addPixelColor(s, i, r, g, b);
             }
        }
    }
}