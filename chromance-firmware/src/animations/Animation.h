#ifndef ANIMATION_H
#define ANIMATION_H

#include <Arduino.h>
#include "../ripple.h"

class AnimationController;

class Animation
{
public:
  Animation(AnimationController &controller) : controller(controller) {}
  virtual ~Animation() {}

  virtual void run() = 0;

protected:
  AnimationController &controller;
};

#endif
