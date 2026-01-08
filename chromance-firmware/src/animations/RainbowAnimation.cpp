#include "RainbowAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"

void RainbowAnimation::run()
{
    controller.getLedController().rainbow();
}
