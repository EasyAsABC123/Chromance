#ifndef HEARTBEAT_ANIMATION_H
#define HEARTBEAT_ANIMATION_H

#include "Animation.h"

class HeartbeatAnimation : public Animation
{
public:
  HeartbeatAnimation(AnimationController &controller) : Animation(controller, Constants::heartbeatEnabled) {}
  void run() override;
  void update() override;

private:
  unsigned long startTime;
};

#endif
