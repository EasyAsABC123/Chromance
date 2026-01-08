#include "StarburstAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"
#include "../LedController.h"

void StarburstAnimation::run()
{
  RippleBehavior behavior = random(2) ? BEHAVIOR_ALWAYS_LEFT : BEHAVIOR_ALWAYS_RIGHT;
  controller.setLastNode(Topology::starburstNode);

  unsigned int baseHue = controller.getBaseColor();

  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    uint32_t color = controller.getLedController().ColorHSV(baseHue + (0xFFFF / 6) * i, 255, 255);

    controller.startRipple(
        Topology::starburstNode,
        i,
        color,
        .65f,
        2600,
        behavior);
  }
}
