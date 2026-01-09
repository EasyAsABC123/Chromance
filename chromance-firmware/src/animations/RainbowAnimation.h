#ifndef RAINBOW_ANIMATION_H
#define RAINBOW_ANIMATION_H

#include "Animation.h"

class RainbowAnimation : public Animation
{
public:
  RainbowAnimation(AnimationController &controller) : Animation(controller, Constants::rainbowEnabled) {}
  void run() override;
  void update() override;

private:
  uint16_t firstHue = 0;
};

#endif
