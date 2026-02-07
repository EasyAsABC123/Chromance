#include "SnakeAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"

REGISTER_ANIMATION(SnakeAnimation)

SnakeAnimation::SnakeAnimation(AnimationController &controller) 
    : Animation(controller), 
      headSegment(-1), 
      headLed(-1), 
      moveDirection(1), 
      targetNode(-1),
      foodSegment(-1),
      foodLed(-1),
      snakeLength(10),
      finished(false)
{
}

bool SnakeAnimation::canBePreempted()
{
    return finished;
}

bool SnakeAnimation::isFinished()
{
    return finished;
}

void SnakeAnimation::spawnFood()
{
    // Simple random spawn
    foodSegment = random(Constants::NUMBER_OF_SEGMENTS);
    foodLed = random(Constants::LEDS_PER_SEGMENT);
}

void SnakeAnimation::run()
{
    body.clear();
    finished = false;
    // Start at a random border node
    int startNode = Topology::borderNodes[random(Topology::numberOfBorderNodes)];
    // Pick a segment
    int k = random(Constants::MAX_PATHS_PER_NODE);
    headSegment = Topology::nodeConnections[startNode][k];
    
    if (headSegment == -1) {
        headSegment = 0; // Fallback
    }
    
    // Determine start LED based on connection
    // If startNode is at side 0 (top), start at led 13 (top). Wait, LED 0 is bottom.
    // Side 0 is Top. Side 1 is Bottom.
    // If we enter from Top (Side 0), we start at LED 13 and go down (-1).
    // If we enter from Bottom (Side 1), we start at LED 0 and go up (+1).
    
    if (Topology::segmentConnections[headSegment][0] == startNode) {
        headLed = Constants::LEDS_PER_SEGMENT - 1;
        moveDirection = -1;
        targetNode = Topology::segmentConnections[headSegment][1];
    } else {
        headLed = 0;
        moveDirection = 1;
        targetNode = Topology::segmentConnections[headSegment][0];
    }
    
    body.push_front({headSegment, headLed});
    snakeLength = 10;
    spawnFood();
}

void SnakeAnimation::update()
{
    if (finished) return;

    // Move every frame? Or every N frames?
    // Let's move every 2 frames for visible speed (30fps -> 15 steps/sec)
    static int frameCount = 0;
    if (frameCount++ % 2 != 0) return;

    // 1. Move Head
    headLed += moveDirection;
    
    bool changedSegment = false;
    
    // Check boundaries
    if (headLed < 0 || headLed >= Constants::LEDS_PER_SEGMENT) {
        // Reached a node!
        int currentNode = targetNode;
        
        // Pick next segment
        // Simple AI: Get closer to food?
        // Food is at (foodSegment, foodLed).
        // Find food Node? (one of the endpoints of foodSegment)
        // Or just navigate nodes using BFS to find path to foodSegment?
        
        // Simplified AI: Just pick a random valid path for now, maybe biased towards food?
        // Let's just do random walk for now to ensure movement works, 
        // implementing full A* on 4000 leds is overkill, but A* on 25 nodes is fast.
        
        // Find food's closest node
        int foodNodeA = Topology::segmentConnections[foodSegment][0];
        int foodNodeB = Topology::segmentConnections[foodSegment][1];
        int targetFoodNode = (random(2) == 0) ? foodNodeA : foodNodeB; 
        
        int pathIdx = Topology::getNextStep(currentNode, targetFoodNode);
        
        int nextSeg = -1;
        if (pathIdx != -1) {
            nextSeg = Topology::nodeConnections[currentNode][pathIdx];
        }
        
        // Fallback or random
        if (nextSeg == -1 || nextSeg == headSegment) {
             int validPaths[6];
             int count = 0;
             for(int k=0; k<Constants::MAX_PATHS_PER_NODE; k++) {
                 int s = Topology::nodeConnections[currentNode][k];
                 if(s >= 0 && s != headSegment) { // Don't go back immediately
                     validPaths[count++] = s;
                 }
             }
             if (count > 0) {
                 nextSeg = validPaths[random(count)];
             } else {
                 nextSeg = headSegment; // Dead end, turn back
             }
        }
        
        headSegment = nextSeg;
        
        // Setup new direction
        if (Topology::segmentConnections[headSegment][0] == currentNode) {
            headLed = Constants::LEDS_PER_SEGMENT - 1;
            moveDirection = -1;
            targetNode = Topology::segmentConnections[headSegment][1];
        } else {
            headLed = 0;
            moveDirection = 1;
            targetNode = Topology::segmentConnections[headSegment][0];
        }
        changedSegment = true;
    }
    
    // Check Collision with Body
    for (const auto& pixel : body) {
        if (pixel.segment == headSegment && pixel.led == headLed) {
            finished = true;
            return;
        }
    }

    // 2. Update Body
    body.push_front({headSegment, headLed});
    
    // Check Food
    if (headSegment == foodSegment && abs(headLed - foodLed) <= 1) {
        snakeLength += 5;
        spawnFood();
    }
    
    // Trim
    while(body.size() > snakeLength) {
        body.pop_back();
    }

    // 3. Draw
    LedController& leds = controller.getLedController();
    leds.clear();
    
    // Draw Food
    leds.setPixelColor(foodSegment, foodLed, 255, 0, 0);
    
    // Draw Body
    for(size_t i=0; i<body.size(); i++) {
        // Gradient green
        int brightness = 255 - (i * 255 / body.size());
        if (brightness < 0) brightness = 0;
        
        leds.setPixelColor(body[i].segment, body[i].led, 0, (uint8_t)brightness, 0);
    }
}
