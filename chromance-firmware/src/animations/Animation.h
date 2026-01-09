#ifndef ANIMATION_H
#define ANIMATION_H

#include <Arduino.h>
#include "../ripple.h"
#include "../Constants.h"

class AnimationController;

class Animation
{
public:
  Animation(AnimationController &controller, bool enabled = true) : controller(controller), enabled(enabled) {}
  virtual ~Animation() {}

  virtual void run() = 0;
  virtual void update() {}
  virtual void stop() {}
  virtual bool canBePreempted() { return true; }
  virtual bool isFinished() { return true; }
  bool isEnabled() const { return enabled; }

protected:
  AnimationController &controller;
  bool enabled;
};

#endif
