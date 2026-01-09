#include "RainbowAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"

void RainbowAnimation::run()
{
    firstHue = 0;
    controller.getLedController().rainbow(firstHue, Constants::RAINBOW_BRIGHTNESS);
}

void RainbowAnimation::update()
{
    firstHue += 1024;
    controller.getLedController().rainbow(firstHue, Constants::RAINBOW_BRIGHTNESS);
}
