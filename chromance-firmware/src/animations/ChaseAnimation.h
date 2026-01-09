#ifndef CHASE_ANIMATION_H
#define CHASE_ANIMATION_H

#include "Animation.h"

class ChaseAnimation : public Animation
{
public:
  ChaseAnimation(AnimationController &controller) : Animation(controller, Constants::chaseEnabled) {}
  void run() override;
  void update() override;
  void stop() override;
  bool isFinished() override;
  const char* getName() const override { return "Chase"; }
};

#endif
