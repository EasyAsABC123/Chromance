#ifndef RAINBOW_PINWHEEL_ANIMATION_H
#define RAINBOW_PINWHEEL_ANIMATION_H

#include "Animation.h"

class RainbowPinwheelAnimation : public Animation
{
public:
  RainbowPinwheelAnimation(AnimationController &controller) : Animation(controller, true) {}
  void run() override;
  void update() override;
  bool isFinished() override { return false; }
  const char *getName() const override { return "Rainbow Pinwheel"; }
  void getConfig(JsonObject &doc) override;
  void setConfig(const JsonObject &doc) override;

private:
  uint16_t baseHue = 0;
  int rotationDirection = 1; // 1 for clockwise, -1 for counterclockwise
  float rotationSpeed = 32.0f; // Units per ms (similar to RainbowAnimation)
};

#endif
