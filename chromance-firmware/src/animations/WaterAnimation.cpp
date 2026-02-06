#include "WaterAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

WaterAnimation::WaterAnimation(AnimationController &controller) 
    : Animation(controller), sourceNode(-1), lastSourceChange(0)
{
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        segmentLevels[i] = 0.0f;
    }
}

void WaterAnimation::run()
{
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        segmentLevels[i] = 0.0f;
    }
    drops.clear();
    sourceNode = random(3);
    lastSourceChange = millis();
}

int WaterAnimation::getDownwardPaths(int nodeIndex, int resultSegments[])
{
    int count = 0;
    int currentY = Topology::nodePositions[nodeIndex].y;

    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        int seg = Topology::nodeConnections[nodeIndex][i];
        if (seg >= 0)
        {
            // Identify the other node
            int nodeA = Topology::segmentConnections[seg][0];
            int nodeB = Topology::segmentConnections[seg][1];
            int otherNode = (nodeA == nodeIndex) ? nodeB : nodeA;
            
            // Check if other node is physically lower (larger Y)
            if (Topology::nodePositions[otherNode].y > currentY) {
                resultSegments[count++] = seg;
            }
        }
    }
    return count;
}

void WaterAnimation::update()
{
    LedController& leds = controller.getLedController();
    std::vector<WaterDrop> nextDrops;
    
    // ----------------------------
    // 1. Spawning Logic
    // ----------------------------
    if (sourceNode == -1 || millis() - lastSourceChange > 5000) {
        sourceNode = random(3);
        lastSourceChange = millis();
    }

    // High spawn rate
    if (random(100) < 30) { 
        int paths[6];
        int count = getDownwardPaths(sourceNode, paths);
        
        if (count > 0) {
            int seg = paths[random(count)];
            
            WaterDrop drop;
            drop.segmentIndex = seg;
            drop.position = 0.0f;
            drop.speed = 0.15f + (random(100)/2000.0f); 
            drop.volume = 0.02f; 
            nextDrops.push_back(drop);
        }
    }

    // ----------------------------
    // 2. Physics Update
    // ----------------------------
    
    // Leakage / Evaporation
    for(int i=0; i<Constants::NUMBER_OF_SEGMENTS; i++) {
        if (segmentLevels[i] > 0.0f) {
            segmentLevels[i] -= 0.005f;
            if (segmentLevels[i] < 0.0f) segmentLevels[i] = 0.0f;
        }
    }

    for (const auto& d_const : drops) {
        WaterDrop d = d_const;
        
        d.position += d.speed;

        // Determine if we hit water in the CURRENT segment
        float waterLevel = segmentLevels[d.segmentIndex];
        // Surface is at (1.0 - waterLevel)
        // If waterLevel is 0.0, surface is 1.0 (bottom of segment)
        
        float surfaceLimit = 1.0f - waterLevel;

        // Check collision with standing water in current segment
        // We allow a small buffer so it doesn't look like it hits 0 immediately if level is tiny
        if (d.position >= surfaceLimit && waterLevel > 0.01f) {
            segmentLevels[d.segmentIndex] += d.volume;
            if (segmentLevels[d.segmentIndex] > 1.0f) segmentLevels[d.segmentIndex] = 1.0f;
            continue; // Absorbed
        }

        // Check if reached bottom of segment (transition point)
        if (d.position >= 1.0f) {
             // We are at the bottom of the segment.
             // Try to move to the next segment.
             
             // 1. Find the node at the bottom
             int bottomNode = Topology::segmentConnections[d.segmentIndex][1]; 
             
             // 2. Find downward paths from this node
             int nextPaths[6];
             int pathCount = getDownwardPaths(bottomNode, nextPaths);
             
             if (pathCount > 0) {
                 // 3. Filter paths that are not full
                 // If a path is full, we can't enter it.
                 int validPaths[6];
                 int validCount = 0;
                 for(int k=0; k<pathCount; k++) {
                     if (segmentLevels[nextPaths[k]] < 1.0f) {
                         validPaths[validCount++] = nextPaths[k];
                     }
                 }
                 
                 if (validCount > 0) {
                     // Decide how many ways to split (1 to validCount)
                     int numToSplit = random(1, validCount + 1);

                     // Shuffle the valid paths to ensure random selection
                     for(int k=0; k<validCount; k++) {
                         int r = random(validCount);
                         int temp = validPaths[k];
                         validPaths[k] = validPaths[r];
                         validPaths[r] = temp;
                     }

                     // Create new drops for the chosen number of paths
                     float newVol = d.volume / numToSplit;
                     for(int k=0; k<numToSplit; k++) {
                         WaterDrop newDrop;
                         newDrop.segmentIndex = validPaths[k];
                         newDrop.position = 0.0f; // Start at top of next segment
                         newDrop.speed = d.speed; 
                         newDrop.volume = newVol;
                         nextDrops.push_back(newDrop);
                     }
                 } else {
                     // All downward paths are full!
                     // Accumulate in current segment (back up)
                     segmentLevels[d.segmentIndex] += d.volume;
                     if (segmentLevels[d.segmentIndex] > 1.0f) segmentLevels[d.segmentIndex] = 1.0f;
                 }
             } else {
                 // No downward paths (Absolute bottom of the map)
                 segmentLevels[d.segmentIndex] += d.volume;
                 if (segmentLevels[d.segmentIndex] > 1.0f) segmentLevels[d.segmentIndex] = 1.0f;
             }
        } else {
            // Still falling within segment
            nextDrops.push_back(d);
        }
    }
    
    drops = nextDrops;

    // ----------------------------
    // 3. Render
    // ----------------------------
    unsigned long time = millis();

    // Clear everything first to ensure black background
    for(int s=0; s<Constants::NUMBER_OF_SEGMENTS; s++) {
        for(int i=0; i<Constants::LEDS_PER_SEGMENT; i++) {
            leds.setPixelColor(s, i, 0, 0, 0);
        }
    }

    for(int s=0; s<Constants::NUMBER_OF_SEGMENTS; s++) {
        // Draw Accumulated Water (Blue)
        if (segmentLevels[s] > 0.001f) {
            int numLit = (int)(segmentLevels[s] * Constants::LEDS_PER_SEGMENT);
            
            // Slosh effect
            if (segmentLevels[s] < 0.99f) {
                NodePosition pA = Topology::nodePositions[Topology::segmentConnections[s][0]];
                float x = pA.x; 
                float slosh = sin(time / 150.0f + x/8.0f) * 1.8f; 
                numLit += (int)slosh;
                if (numLit < 0) numLit = 0;
                if (numLit > Constants::LEDS_PER_SEGMENT) numLit = Constants::LEDS_PER_SEGMENT;
            }

            for(int i=0; i<numLit; i++) {
                // LED 0 is Bottom. LED 13 is Top.
                // Fill from 0 up to numLit.
                // Brighter Blue (0, 0, 150)
                leds.setPixelColor(s, i, 0, 0, 150); 
                
                // Surface foam (Cyan/White) - Brighter (100, 100, 180)
                if (i >= numLit - 2 && i < numLit) {
                     leds.setPixelColor(s, i, 100, 100, 180);
                }
            }
        }
    }

    // Draw Drops (Cyan/White) - Brighter (150, 220, 255)
    for (const auto& d : drops) {
        // d.position 0.0 -> Top (LED 13)
        // d.position 1.0 -> Bottom (LED 0)
        
        int ledIndex = (int)((1.0f - d.position) * (Constants::LEDS_PER_SEGMENT - 1));
        if (ledIndex < 0) ledIndex = 0;
        if (ledIndex >= Constants::LEDS_PER_SEGMENT) ledIndex = Constants::LEDS_PER_SEGMENT - 1;
        
        // Drop brightness: Brighter
        leds.setPixelColor(d.segmentIndex, ledIndex, 150, 220, 255);
        
        // Trail brightness: Brighter (0, 100, 180)
        if (ledIndex + 1 < Constants::LEDS_PER_SEGMENT) {
             leds.setPixelColor(d.segmentIndex, ledIndex + 1, 0, 100, 180);
        }
    }
}
#include "../AnimationRegistry.h"
REGISTER_ANIMATION(WaterAnimation)
