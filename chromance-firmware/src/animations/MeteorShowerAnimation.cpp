#include "MeteorShowerAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void MeteorShowerAnimation::run()
{
    Ripple::runnerNode = 24; // Target the bottom node

    // Pick a random top node (0, 1, or 2)
    int startNode = random(3);

    // Identify valid paths for the chosen node.
    // Based on Topology.cpp:
    // Node 0: indices 2, 4 are valid.
    // Node 1: indices 2, 4 are valid.
    // Node 2: indices 2, 4 are valid.
    // We can pick either 2 or 4 randomly.
    int direction = random(2) ? 2 : 4;

    // Verify connection just in case (though we know the topology)
    if (Topology::nodeConnections[startNode][direction] < 0)
    {
        // Fallback to finding the first valid connection
        for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
        {
            if (Topology::nodeConnections[startNode][i] >= 0)
            {
                direction = i;
                break;
            }
        }
    }

    // Meteor color: White/Blueish with high brightness
    // Varied slightly
    uint8_t hue = 140 + random(40); // Cyan/Blue range (approx 128 is Cyan, 170 Blue)
    // Actually using 0-255 hue in HSV usually, or 0-65535 depending on lib.
    // LedController::ColorHSV takes (hue, sat, val). 
    // If controller.getLedController().ColorHSV uses 16-bit hue (0-65535), 
    // Blue is ~43690. Cyan is ~32768.
    // Let's use the controller's helper if unsure, or standard HSV.
    // Existing code uses `controller.getLedController().ColorHSV(baseHue + ..., 255, 255)`
    // where baseHue is 0-65535.
    
    // Let's go for a cool white/cyan mix.
    // Saturation 0-50 for white-ish, or 255 for full color.
    // Let's make them bright white with a tint.
    uint32_t color = controller.getLedController().ColorHSV(random(30000, 45000), random(50, 150), 255);

    // Occasionally pure white
    if (random(5) == 0) {
        color = 0xFFFFFF;
    }

    controller.startRipple(
        startNode,
        direction,
        color,
        0.8f,  // Fast speed
        3500,  // Long enough to reach bottom
        BEHAVIOR_CHASE
    );
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(MeteorShowerAnimation)
