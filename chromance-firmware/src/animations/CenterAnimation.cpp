#include "CenterAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void CenterAnimation::run()
{
    unsigned int startingNode = Topology::starburstNode;

    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
        if (Topology::nodeConnections[startingNode][i] >= 0)
        {
            controller.startRipple(
                startingNode,
                i,
                controller.getLedController().ColorHSV(controller.getBaseColor(), 255, 50),
                controller.getSpeed(),
                5000,
                BEHAVIOR_FEISTY);
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(CenterAnimation)
