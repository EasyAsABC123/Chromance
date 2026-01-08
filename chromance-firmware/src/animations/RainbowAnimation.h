#ifndef RAINBOW_ANIMATION_H
#define RAINBOW_ANIMATION_H

#include "Animation.h"

class RainbowAnimation : public Animation
{
public:
  RainbowAnimation(AnimationController &controller) : Animation(controller) {}
  void run() override;
};

#endif
