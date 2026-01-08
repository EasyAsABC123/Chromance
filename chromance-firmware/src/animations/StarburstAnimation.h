#ifndef STARBURST_ANIMATION_H
#define STARBURST_ANIMATION_H

#include "Animation.h"

class StarburstAnimation : public Animation
{
public:
  StarburstAnimation(AnimationController &controller) : Animation(controller) {}
  void run() override;
};

#endif
