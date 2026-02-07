#include "LightningAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"

REGISTER_ANIMATION(LightningAnimation)

LightningAnimation::LightningAnimation(AnimationController &controller) : Animation(controller)
{
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) flashIntensity[i] = 0.0f;
    nextStrikeTime = 0;
}

void LightningAnimation::run()
{
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) flashIntensity[i] = 0.0f;
    nextStrikeTime = millis() + random(100, 1000);
}

void LightningAnimation::update()
{
    // Fade out
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        if(flashIntensity[i] > 0.0f) {
            flashIntensity[i] -= 0.05f; // Fast fade
            if(flashIntensity[i] < 0.0f) flashIntensity[i] = 0.0f;
        }
    }

    if (millis() >= nextStrikeTime) {
        // Strike!
        int currentNode = random(3); // Start at top (0, 1, 2)
        
        // Create a path down
        while (true) {
            // Find connected segments going down
            int possibleSegments[6];
            int count = 0;
            
            for(int k=0; k<Constants::MAX_PATHS_PER_NODE; k++) {
                int seg = Topology::nodeConnections[currentNode][k];
                if(seg >= 0) {
                    int other = (Topology::segmentConnections[seg][0] == currentNode) ? 
                                 Topology::segmentConnections[seg][1] : 
                                 Topology::segmentConnections[seg][0];
                    
                    if(Topology::nodePositions[other].y > Topology::nodePositions[currentNode].y) {
                        possibleSegments[count++] = seg;
                    }
                }
            }
            
            if(count == 0) break; // Reached bottom
            
            // Pick one
            int chosenSeg = possibleSegments[random(count)];
            flashIntensity[chosenSeg] = 1.0f;
            
            // Move to next node
            currentNode = (Topology::segmentConnections[chosenSeg][0] == currentNode) ? 
                           Topology::segmentConnections[chosenSeg][1] : 
                           Topology::segmentConnections[chosenSeg][0];
                           
            // Chance to branch?
            if (random(100) < 30 && count > 1) {
                 // Pick another branch
                 int branchSeg = possibleSegments[random(count)];
                 if (branchSeg != chosenSeg) {
                     flashIntensity[branchSeg] = 0.8f; 
                     // We don't follow the branch logic fully to keep recursion simple here, just light the segment
                 }
            }
        }
        
        nextStrikeTime = millis() + random(200, 1500); // Random delay
        
        // Sometimes double strike
        if(random(100) < 20) nextStrikeTime = millis() + random(50, 150);
    }

    LedController& leds = controller.getLedController();
    for(int s=0; s<Constants::NUMBER_OF_SEGMENTS; s++) {
        if(flashIntensity[s] > 0.001f) {
            // White to Purple fade
            // 1.0 -> White
            // 0.5 -> Purple
            // 0.0 -> Black
            
            byte r, g, b;
            if(flashIntensity[s] > 0.5f) {
                // White to Purple
                // P: 150, 0, 255
                // W: 255, 255, 255
                float t = (flashIntensity[s] - 0.5f) * 2.0f;
                r = 150 + (byte)(105 * t);
                g = (byte)(255 * t);
                b = 255;
            } else {
                // Purple to Black
                float t = flashIntensity[s] * 2.0f;
                r = (byte)(150 * t);
                g = 0;
                b = (byte)(255 * t);
            }
            
            for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
                leds.setPixelColor(s, i, r, g, b);
            }
        } else {
             // Ensure black background
             for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
                leds.setPixelColor(s, i, 0, 0, 0);
            }
        }
    }
}
