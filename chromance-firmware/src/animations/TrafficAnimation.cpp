#include "TrafficAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"

REGISTER_ANIMATION(TrafficAnimation)

TrafficAnimation::TrafficAnimation(AnimationController &controller) : Animation(controller)
{
    for(int i=0; i<Constants::NUMBER_OF_NODES; i++) nodeOccupied[i] = false;
}

bool TrafficAnimation::canBePreempted()
{
    return true;
}

bool TrafficAnimation::isFinished()
{
    return false;
}

void TrafficAnimation::run()
{
    cars.clear();
    for(int i=0; i<Constants::NUMBER_OF_NODES; i++) nodeOccupied[i] = false;
}

void TrafficAnimation::update()
{
    // Spawn cars
    if (cars.size() < 100 && random(100) < 40) {
        // Pick random border node
        int startNode = Topology::borderNodes[random(Topology::numberOfBorderNodes)];
        
        // Pick path
        int k = random(Constants::MAX_PATHS_PER_NODE);
        int seg = Topology::nodeConnections[startNode][k];
        if (seg >= 0) {
            Car c;
            c.segment = seg;
            // Determine direction: if node at 0 is start, pos 0.0. Else 1.0.
            bool startAtZero = (Topology::segmentConnections[seg][1] == startNode); // wait, Side 1 is bottom.
            // Wait, logic:
            // Side 0: Top node. Side 1: Bottom node.
            // If startNode is Top (Side 0), pos starts 0.0 (top) moves to 1.0 (bottom).
            // If startNode is Bottom (Side 1), pos starts 1.0 (bottom) moves to 0.0 (top).
            
            c.position = (Topology::segmentConnections[seg][0] == startNode) ? 0.0f : 1.0f;
            c.speed = (c.position == 0.0f) ? 0.02f : -0.02f;
            // Use random hue for each car
            c.color = controller.getLedController().ColorHSV(random(65536), 255, 255);
            c.waiting = false;
            c.nextSegment = -1;
            cars.push_back(c);
        }
    }

    std::vector<Car> nextCars;
    
    // Reset node occupancy for next frame calc
    // But we need persistence for locking.
    // Let's assume nodes are free unless a car is IN them or entering them.
    // Simplified: Car reserves node when close.
    
    for(auto& c : cars) {
        float distToNode = (c.speed > 0) ? (1.0f - c.position) : c.position;
        
        if (distToNode < 0.1f && !c.waiting) {
            // Approaching intersection
            int targetNode = (c.speed > 0) ? Topology::segmentConnections[c.segment][1] : Topology::segmentConnections[c.segment][0];
            
            // Check if blocked
            if (nodeOccupied[targetNode]) {
                c.waiting = true;
            } else {
                nodeOccupied[targetNode] = true; // Lock it
                // Pick next path
                int attempts = 0;
                while (attempts < 10) {
                    int k = random(Constants::MAX_PATHS_PER_NODE);
                    int nextSeg = Topology::nodeConnections[targetNode][k];
                    if (nextSeg >= 0 && nextSeg != c.segment) {
                        c.nextSegment = nextSeg;
                        break;
                    }
                    attempts++;
                }
            }
        }
        
        if (!c.waiting) {
            c.position += c.speed;
            
            // Check transition
            if ((c.speed > 0 && c.position >= 1.0f) || (c.speed < 0 && c.position <= 0.0f)) {
                // Arrived at node
                int arriveNode = (c.speed > 0) ? Topology::segmentConnections[c.segment][1] : Topology::segmentConnections[c.segment][0];
                nodeOccupied[arriveNode] = false; // Release lock
                
                if (c.nextSegment != -1) {
                    c.segment = c.nextSegment;
                    // Determine new start pos
                    bool startAtZero = (Topology::segmentConnections[c.segment][0] == arriveNode);
                    c.position = startAtZero ? 0.0f : 1.0f;
                    c.speed = startAtZero ? 0.02f : -0.02f;
                    c.nextSegment = -1;
                } else {
                    // Despawn (dead end or bad luck)
                    continue; 
                }
            }
        } else {
            // Check if free now
             int targetNode = (c.speed > 0) ? Topology::segmentConnections[c.segment][1] : Topology::segmentConnections[c.segment][0];
             if (!nodeOccupied[targetNode]) {
                 c.waiting = false;
                 nodeOccupied[targetNode] = true;
             }
        }
        
        nextCars.push_back(c);
    }
    
    cars = nextCars;

    LedController& leds = controller.getLedController();
    leds.clear();
    
    for(const auto& c : cars) {
        // Map position (0.0=Top, 1.0=Bottom) to LEDs
        // LED 0 is Bottom, LED 13 is Top
        // So pos 0.0 -> LED 13, pos 1.0 -> LED 0
        int ledIdx = (int)((1.0f - c.position) * (Constants::LEDS_PER_SEGMENT - 1));
        
        // Clamp
        if (ledIdx < 0) ledIdx = 0;
        if (ledIdx >= Constants::LEDS_PER_SEGMENT) ledIdx = Constants::LEDS_PER_SEGMENT - 1;
        
        byte r = (byte)((c.color >> 16) & 0xFF);
        byte g = (byte)((c.color >> 8) & 0xFF);
        byte b = (byte)(c.color & 0xFF);
        
        leds.setPixelColor(c.segment, ledIdx, r, g, b);
        // Headlights?
    }
}
