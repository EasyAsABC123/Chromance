#include "RandomAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void RandomAnimation::run()
{
    int node = Topology::funNodes[random(Topology::numberOfFunNodes)];
    while (node == controller.getLastNode())
    {
        node = Topology::funNodes[random(Topology::numberOfFunNodes)];
    }
    controller.setLastNode(node);

    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        if (Topology::nodeConnections[node][i] >= 0)
        {
            controller.startRipple(
                node,
                i,
                controller.getRandomColor(),
                float(random(100)) / 100.0f * .2f + .5f,
                Constants::ANIMATION_TIME,
                BEHAVIOR_FEISTY);
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(RandomAnimation)
