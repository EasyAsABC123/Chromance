#ifndef RANDOM_ANIMATION_H
#define RANDOM_ANIMATION_H

#include "Animation.h"

class RandomAnimation : public Animation
{
public:
  RandomAnimation(AnimationController &controller) : Animation(controller, Constants::randomPulsesEnabled) {}
  void run() override;
  const char* getName() const override { return "Random Pulse"; }
};

#endif
