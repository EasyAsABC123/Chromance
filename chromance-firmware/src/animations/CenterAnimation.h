#ifndef CENTER_ANIMATION_H
#define CENTER_ANIMATION_H

#include "Animation.h"

class CenterAnimation : public Animation
{
public:
  CenterAnimation(AnimationController &controller) : Animation(controller, Constants::centerPulseEnabled) {}
  void run() override;
  const char *getName() const override { return "Center Pulse"; }
};

#endif
