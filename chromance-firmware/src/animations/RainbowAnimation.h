#ifndef RAINBOW_ANIMATION_H
#define RAINBOW_ANIMATION_H

#include "Animation.h"

class RainbowAnimation : public Animation
{
public:
  RainbowAnimation(AnimationController &controller) : Animation(controller, Constants::rainbowEnabled) {}
  void run() override;
  void update() override;
  bool isFinished() override { return false; }
  const char *getName() const override { return "Rainbow"; }
  void getConfig(JsonObject &doc) override;
  void setConfig(const JsonObject &doc) override;

private:
  uint16_t firstHue = 0;
  int brightness = Constants::RAINBOW_BRIGHTNESS;
};

#endif
