#ifndef RAINBOW_RADIATE_ANIMATION_H
#define RAINBOW_RADIATE_ANIMATION_H

#include "Animation.h"

class RainbowRadiateAnimation : public Animation
{
public:
  RainbowRadiateAnimation(AnimationController &controller) : Animation(controller, true) {}
  void run() override;
  void update() override;
  bool isFinished() override { return false; }
  const char *getName() const override { return "Rainbow Radiate"; }

private:
  float animationPhase = 0.0f;
  float radiateSpeed = 32.0f; // Units per ms (similar to RainbowAnimation)
  float maxDistance = 0.0f; // Will be calculated in run()
};

#endif
