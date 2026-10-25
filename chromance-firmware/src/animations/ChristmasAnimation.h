#ifndef CHRISTMAS_ANIMATION_H
#define CHRISTMAS_ANIMATION_H

#include "Animation.h"
#include <stdint.h>

class ChristmasAnimation : public Animation {
public:
  explicit ChristmasAnimation(AnimationController &controller)
      : Animation(controller, true) {}

  void run() override;
  void update() override;
  const char *getName() const override { return "Christmas"; }
  bool isFinished() override { return false; }

private:
  uint8_t chooseBrightness();

  uint8_t colorIndex[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT] = {};
  uint8_t brightness[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT] = {};
  uint8_t targetBrightness[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT] = {};
  uint32_t nextChange[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT] = {};
  uint32_t sparkleUntil[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT] = {};
  bool sparkleActive[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT] = {};

  uint32_t nextTempoChange = 0;
  bool tempoFast = false;
};

#endif
