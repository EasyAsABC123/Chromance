#include "CubeAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void CubeAnimation::run()
{
    int node = Topology::cubeNodes[random(Topology::numberOfCubeNodes)];
    while (node == controller.getLastNode())
    {
        node = Topology::cubeNodes[random(Topology::numberOfCubeNodes)];
    }
    controller.setLastNode(node);

    RippleBehavior behavior = random(2) ? BEHAVIOR_ALWAYS_LEFT : BEHAVIOR_ALWAYS_RIGHT;

    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        if (Topology::nodeConnections[node][i] >= 0)
        {
            controller.startRipple(
                node,
                i,
                controller.getRandomColor(),
                .8f,
                Constants::ANIMATION_TIME,
                behavior);
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(CubeAnimation)
