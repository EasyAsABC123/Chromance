#ifndef CUBE_ANIMATION_H
#define CUBE_ANIMATION_H

#include "Animation.h"

class CubeAnimation : public Animation
{
public:
  CubeAnimation(AnimationController &controller) : Animation(controller, Constants::cubePulsesEnabled) {}
  void run() override;
  const char* getName() const override { return "Cube Pulse"; }
};

#endif
