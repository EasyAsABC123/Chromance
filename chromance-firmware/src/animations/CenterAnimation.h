#ifndef CENTER_ANIMATION_H
#define CENTER_ANIMATION_H

#include "Animation.h"

class CenterAnimation : public Animation
{
public:
  CenterAnimation(AnimationController &controller) : Animation(controller) {}
  void run() override;
};

#endif
