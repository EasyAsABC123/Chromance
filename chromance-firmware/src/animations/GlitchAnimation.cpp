#include "GlitchAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void GlitchAnimation::run()
{
    // Can trigger a single big glitch here if called manually
}

void GlitchAnimation::update()
{
    // Randomly trigger sparks
    // Chance per frame. If 60fps, 5% is ~3 sparks/sec.
    if (random(100) < 5) 
    {
        int node = random(Constants::NUMBER_OF_NODES);
        
        // Pick a random connected segment (direction)
        int attempts = 0;
        int direction = -1;
        while(attempts < 6) {
             int d = random(Constants::MAX_PATHS_PER_NODE);
             if (Topology::nodeConnections[node][d] >= 0) {
                 direction = d;
                 break;
             }
             attempts++;
        }

        if (direction >= 0) {
            // Random glitch color: White, Red, or random Hue
            uint32_t color;
            int r = random(3);
            if (r == 0) color = 0xFFFFFF; // White
            else if (r == 1) color = 0xFF0000; // Red
            else color = controller.getRandomColor();

            controller.startRipple(
                node,
                direction,
                color,
                1.5f,  // Very fast
                150,   // Very short life (ms)
                BEHAVIOR_COUCH_POTATO // Stay in place (or minimal movement)
            );
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(GlitchAnimation)
