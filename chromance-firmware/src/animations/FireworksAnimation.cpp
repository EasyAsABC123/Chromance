#include "FireworksAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

FireworksAnimation::FireworksAnimation(AnimationController &controller) : Animation(controller) {}

void FireworksAnimation::run()
{
    exploding = false;
    launchRippleIndex = -1;
    
    // Pick target: random upper node
    targetNode = random(15); // Top half nodes
    Ripple::runnerNode = targetNode;
    
    // Find a free ripple
    for(int i=0; i<Constants::NUMBER_OF_RIPPLES; i++) {
        if (controller.getRipple(i).state == STATE_DEAD) {
            launchRippleIndex = i;
            break;
        }
    }
    
    if (launchRippleIndex >= 0) {
        // Launch from bottom
        // Node 24 is bottom.
        // Find direction UP.
        int direction = 0; // Default
        for(int k=0; k<Constants::MAX_PATHS_PER_NODE; k++) {
            if (Topology::nodeConnections[24][k] >= 0) {
                direction = k;
                break;
            }
        }
        
        controller.getRipple(launchRippleIndex).start(
            24, 
            direction, 
            0xFFFFFF, // White rocket
            0.6f, 
            3000, 
            BEHAVIOR_CHASE
        );
    }
}

void FireworksAnimation::update()
{
    if (!exploding) {
        if (launchRippleIndex >= 0) {
            Ripple& r = controller.getRipple(launchRippleIndex);
            
            // Check if reached target
            if (r.node == targetNode) {
                // EXPLODE!
                exploding = true;
                
                // Kill the rocket
                r.state = STATE_DEAD;
                
                // Spawn particles
                uint32_t color = controller.getRandomColor();
                
                // Iterate all directions
                for (int i=0; i<Constants::MAX_PATHS_PER_NODE; i++) {
                    if (Topology::nodeConnections[targetNode][i] >= 0) {
                        controller.startRipple(
                            targetNode,
                            i,
                            color,
                            0.5f,
                            1500, // Short life
                            BEHAVIOR_ALWAYS_LEFT // Or EXPLODING (which just picks random wide turns)
                        );
                    }
                }
            }
            else if (r.state == STATE_DEAD) {
                // Rocket failed or died? Restart
                run();
            }
        }
    } else {
        // Check if all ripples are dead to restart?
        // Or just wait a bit?
        if (controller.getActiveRippleCount() == 0) {
            if (random(100) < 5) run(); // Restart chance
        }
    }
}
