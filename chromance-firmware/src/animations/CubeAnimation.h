#ifndef CUBE_ANIMATION_H
#define CUBE_ANIMATION_H

#include "Animation.h"

class CubeAnimation : public Animation
{
public:
  CubeAnimation(AnimationController &controller) : Animation(controller) {}
  void run() override;
};

#endif
