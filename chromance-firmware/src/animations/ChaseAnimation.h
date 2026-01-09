#ifndef CHASE_ANIMATION_H
#define CHASE_ANIMATION_H

#include "Animation.h"

class ChaseAnimation : public Animation
{
public:
  ChaseAnimation(AnimationController &controller) : Animation(controller) {}
  void run() override;
  void update() override;
  void stop() override;
};

#endif
