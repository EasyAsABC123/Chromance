#ifndef HEARTBEAT_ANIMATION_H
#define HEARTBEAT_ANIMATION_H

#include "Animation.h"

class HeartbeatAnimation : public Animation
{
public:
  HeartbeatAnimation(AnimationController &controller) : Animation(controller, Constants::heartbeatEnabled) {}
  void run() override;
  void update() override;
  bool isFinished() override;
  bool canBePreempted() override;
  const char *getName() const override { return "Heartbeat"; }

private:
  unsigned long startTime;
};

#endif
