#include "CenterAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void CenterAnimation::run()
{
    unsigned int startingNode = Topology::starburstNode;
    RippleBehavior behavior = random(2) ? BEHAVIOR_ALWAYS_LEFT : BEHAVIOR_ALWAYS_RIGHT;

    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        if (Topology::nodeConnections[startingNode][i] >= 0)
        {
            controller.startRipple(
                startingNode,
                i,
                controller.getRandomColor(),
                controller.getSpeed(),
                5000,
                behavior);
        }
    }
}
