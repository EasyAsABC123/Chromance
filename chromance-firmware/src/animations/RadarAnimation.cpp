#include "RadarAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"
#include <cmath>

REGISTER_ANIMATION(RadarAnimation)

bool RadarAnimation::canBePreempted()
{
    return true;
}

bool RadarAnimation::isFinished()
{
    return false;
}

void RadarAnimation::run()
{
    angle = 0.0f;
    for(int i=0; i<Constants::NUMBER_OF_NODES; i++) nodeBrightness[i] = 0.0f;
}

void RadarAnimation::update()
{
    angle += 0.05f; // Rotation speed
    if(angle > 6.28f) angle -= 6.28f;
    
    NodePosition center = Topology::nodePositions[15];
    
    // Check for pings
    for(int i=0; i<Constants::NUMBER_OF_NODES; i++) {
        float dx = Topology::nodePositions[i].x - center.x;
        float dy = Topology::nodePositions[i].y - center.y;
        float nodeAngle = atan2(dy, dx);
        if (nodeAngle < 0) nodeAngle += 6.28f;
        
        // Check if sweep line passed node
        float diff = angle - nodeAngle;
        if (abs(diff) < 0.1f) {
            nodeBrightness[i] = 1.0f;
        }
        
        // Decay
        if (nodeBrightness[i] > 0.0f) {
            nodeBrightness[i] -= 0.02f;
            if (nodeBrightness[i] < 0.0f) nodeBrightness[i] = 0.0f;
        }
    }
    
    LedController& leds = controller.getLedController();
    leds.clear();
    
    // Draw sweep
    // Iterate all segments/pixels
    for(int s=0; s<Constants::NUMBER_OF_SEGMENTS; s++) {
        // Calculate angle of segment
        int n0 = Topology::segmentConnections[s][0];
        int n1 = Topology::segmentConnections[s][1];
        float x0 = Topology::nodePositions[n0].x;
        float y0 = Topology::nodePositions[n0].y;
        float x1 = Topology::nodePositions[n1].x;
        float y1 = Topology::nodePositions[n1].y;
        
        // Draw structure ghost if nodes are lit
        float b0 = nodeBrightness[n0];
        float b1 = nodeBrightness[n1];
        
        if (b0 > 0.0f || b1 > 0.0f) {
            for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
                float t = (float)i / (Constants::LEDS_PER_SEGMENT - 1);
                float bright = b1 + (b0 - b1) * t; // Interpolate brightness
                
                if (bright > 0.01f) {
                    leds.setPixelColor(s, i, 0, (byte)(bright*255), 0);
                }
            }
        }
    }
}
