#include "RainbowAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"

void RainbowAnimation::run()
{
    firstHue = 0;
    controller.getLedController().rainbow(firstHue);
}

void RainbowAnimation::update()
{
    firstHue += 1024;
    controller.getLedController().rainbow(firstHue);
}
