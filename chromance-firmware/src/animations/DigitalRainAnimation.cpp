#include "DigitalRainAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"

REGISTER_ANIMATION(DigitalRainAnimation)

bool DigitalRainAnimation::canBePreempted()
{
    return finished;
}

bool DigitalRainAnimation::isFinished()
{
    return finished;
}

void DigitalRainAnimation::run()
{
    drops.clear();
    finished = false;
    stopping = false;
    startTime = millis();
}

void DigitalRainAnimation::update()
{
    if (finished) return;

    if (!stopping && millis() - startTime > 10000) {
        stopping = true;
    }

    // Spawn
    if (!stopping && random(100) < 40) {
        // Pick top segment? Or segment connected to top node?
        // Top nodes: 0, 1, 2
        int startNode = random(3);
        
        // Find downward path
        for(int k=0; k<Constants::MAX_PATHS_PER_NODE; k++) {
            int seg = Topology::nodeConnections[startNode][k];
            if (seg >= 0) {
                // Check if downward
                int other = (Topology::segmentConnections[seg][0] == startNode) ? Topology::segmentConnections[seg][1] : Topology::segmentConnections[seg][0];
                if (Topology::nodePositions[other].y > Topology::nodePositions[startNode].y) {
                    RainDrop d;
                    d.segment = seg;
                    d.position = 0.0f;
                    d.speed = 0.05f + (random(50)/1000.0f);
                    drops.push_back(d);
                    break; 
                }
            }
        }
    }

    LedController& leds = controller.getLedController();
    leds.clear();

    std::vector<RainDrop> nextDrops;
    for(auto d : drops) {
        d.position += d.speed;
        
        if (d.position >= 1.0f) {
            // Move to next segment
            int bottomNode = Topology::segmentConnections[d.segment][1]; // Side 1 is bottom
            
            // Find downward paths
            std::vector<int> paths;
            for(int k=0; k<Constants::MAX_PATHS_PER_NODE; k++) {
                int seg = Topology::nodeConnections[bottomNode][k];
                if (seg >= 0 && seg != d.segment) {
                    int other = (Topology::segmentConnections[seg][0] == bottomNode) ? Topology::segmentConnections[seg][1] : Topology::segmentConnections[seg][0];
                    if (Topology::nodePositions[other].y > Topology::nodePositions[bottomNode].y) {
                        paths.push_back(seg);
                    }
                }
            }
            
            if (!paths.empty()) {
                d.segment = paths[random(paths.size())];
                d.position = 0.0f;
                nextDrops.push_back(d);
            }
            // Else die (fall off bottom)
        } else {
            nextDrops.push_back(d);
        }
        
        // Draw
        int ledIdx = (int)((1.0f - d.position) * (Constants::LEDS_PER_SEGMENT - 1));
        if (ledIdx >= 0 && ledIdx < Constants::LEDS_PER_SEGMENT) {
            // Bright head
            leds.setPixelColor(d.segment, ledIdx, 150, 255, 150);
            
            // Trail
            for(int i=1; i<5; i++) {
                int trailIdx = ledIdx + i;
                if (trailIdx < Constants::LEDS_PER_SEGMENT) {
                    int bright = 100 - (i * 20);
                    leds.setPixelColor(d.segment, trailIdx, 0, bright, 0);
                }
            }
        }
    }
    drops = nextDrops;

    if (stopping && drops.empty()) {
        finished = true;
    }
}
