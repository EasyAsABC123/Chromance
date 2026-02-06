#include "BouncingBallsAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include <cmath>

BouncingBallsAnimation::BouncingBallsAnimation(AnimationController &controller) : Animation(controller) {}

void BouncingBallsAnimation::run()
{
    balls.clear();
    // Spawn initial balls
    for(int i=0; i<5; i++) {
        Ball b;
        b.segmentIndex = random(Constants::NUMBER_OF_SEGMENTS); // Random start? Or top?
        // Let's spawn at top nodes
        int topNodes[] = {0, 1, 2};
        int node = topNodes[random(3)];
        
        int paths[6];
        int count = getDownwardPaths(node, paths);
        if (count > 0) {
            b.segmentIndex = paths[random(count)];
            b.position = 0.0f;
            b.velocity = 0.0f;
            b.color = controller.getRandomColor();
            b.dying = false;
            balls.push_back(b);
        }
    }
}

int BouncingBallsAnimation::getDownwardPaths(int nodeIndex, int resultSegments[])
{
    int count = 0;
    int currentY = Topology::nodePositions[nodeIndex].y;
    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        int seg = Topology::nodeConnections[nodeIndex][i];
        if (seg >= 0)
        {
            int otherNode = (Topology::segmentConnections[seg][0] == nodeIndex) 
                            ? Topology::segmentConnections[seg][1] 
                            : Topology::segmentConnections[seg][0];
            if (Topology::nodePositions[otherNode].y > currentY) {
                resultSegments[count++] = seg;
            }
        }
    }
    return count;
}

int BouncingBallsAnimation::getUpwardPaths(int nodeIndex, int resultSegments[])
{
    int count = 0;
    int currentY = Topology::nodePositions[nodeIndex].y;
    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        int seg = Topology::nodeConnections[nodeIndex][i];
        if (seg >= 0)
        {
            int otherNode = (Topology::segmentConnections[seg][0] == nodeIndex) 
                            ? Topology::segmentConnections[seg][1] 
                            : Topology::segmentConnections[seg][0];
            if (Topology::nodePositions[otherNode].y < currentY) {
                resultSegments[count++] = seg;
            }
        }
    }
    return count;
}

void BouncingBallsAnimation::update()
{
    float gravity = 0.005f;
    float restitution = 0.8f;
    
    std::vector<Ball> nextBalls;

    // Maintenance: ensure min ball count
    if (balls.size() < 3 && random(100) < 5) {
         Ball b;
         int topNodes[] = {0, 1, 2};
         int node = topNodes[random(3)];
         int paths[6];
         int count = getDownwardPaths(node, paths);
         if (count > 0) {
            b.segmentIndex = paths[random(count)];
            b.position = 0.0f;
            b.velocity = 0.0f;
            b.color = controller.getRandomColor();
            b.dying = false;
            nextBalls.push_back(b);
         }
    }

    for (const auto& b_const : balls) {
        Ball b = b_const;
        
        b.velocity += gravity;
        b.position += b.velocity;
        
        // 1. Hit Bottom of Segment (position >= 1.0)
        if (b.position >= 1.0f) {
            int bottomNode = Topology::segmentConnections[b.segmentIndex][1]; // Bottom node
            
            // Check if we can go further down
            int downPaths[6];
            int downCount = getDownwardPaths(bottomNode, downPaths);
            
            if (downCount > 0) {
                // Continue falling
                b.segmentIndex = downPaths[random(downCount)];
                b.position = 0.0f;
            } else {
                // Bounce!
                b.position = 1.0f;
                b.velocity = -b.velocity * restitution;
                
                // If velocity is too low, die or respawn
                if (std::abs(b.velocity) < 0.02f) {
                    // Dead
                    continue; // Don't add to nextBalls
                }
            }
        }
        // 2. Hit Top of Segment (position <= 0.0) - Moving Up
        else if (b.position <= 0.0f) {
            int topNode = Topology::segmentConnections[b.segmentIndex][0]; // Top node
            
            // Check if we can go further up
            int upPaths[6];
            int upCount = getUpwardPaths(topNode, upPaths);
            
            if (upCount > 0) {
                // Continue moving up
                b.segmentIndex = upPaths[random(upCount)];
                b.position = 1.0f;
            } else {
                // Hit ceiling? Bounce down (rare) or just zero velocity
                b.position = 0.0f;
                b.velocity = -b.velocity * 0.5f; // Lose more energy on ceiling
            }
        }
        
        nextBalls.push_back(b);
    }
    
    balls = nextBalls;

    // Render
    LedController& lc = controller.getLedController();
    for (const auto& b : balls) {
        int ledIdx = (int)((1.0f - b.position) * (Constants::LEDS_PER_SEGMENT - 1));
        if (ledIdx < 0) ledIdx = 0;
        if (ledIdx >= Constants::LEDS_PER_SEGMENT) ledIdx = Constants::LEDS_PER_SEGMENT - 1;
        
        byte r = (b.color >> 16) & 0xFF;
        byte g = (b.color >> 8) & 0xFF;
        byte bl = b.color & 0xFF;
        
        lc.addPixelColor(b.segmentIndex, ledIdx, r, g, bl);
        // Add trail?
        if (std::abs(b.velocity) > 0.1f) {
             // Draw one pixel behind
             int trailIdx = ledIdx + (b.velocity > 0 ? 1 : -1);
             if (trailIdx >= 0 && trailIdx < Constants::LEDS_PER_SEGMENT)
                 lc.addPixelColor(b.segmentIndex, trailIdx, r/2, g/2, bl/2);
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(BouncingBallsAnimation)
