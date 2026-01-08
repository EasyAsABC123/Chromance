#ifndef RANDOM_ANIMATION_H
#define RANDOM_ANIMATION_H

#include "Animation.h"

class RandomAnimation : public Animation
{
public:
  RandomAnimation(AnimationController &controller) : Animation(controller) {}
  void run() override;
};

#endif
