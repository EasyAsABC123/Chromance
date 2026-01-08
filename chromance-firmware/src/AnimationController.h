#ifndef ANIMATIONCONTROLLER_H
#define ANIMATIONCONTROLLER_H

#include <Arduino.h>
#include "Constants.h"
#include "LedController.h"
#include "ripple.h"
#include "Topology.h"

class AnimationController
{
public:
  AnimationController(LedController &ledController);
  void init();
  void update(); // Main loop update (advance animations)

private:
  LedController &ledController;
  Ripple ripples[Constants::NUMBER_OF_RIPPLES];

  unsigned int baseColor;
  unsigned long lastRandomPulse;

  byte currentAutoPulseType = 255;
  unsigned long lastAutoPulseChange;
  byte lastAutoPulseNode = 255;

  // Auto pulse types count
  byte numberOfAutoPulseTypes;

  void getNextAnimation();
  void startAnimation(byte animation);

  void randomPulse();
  void cubePulse();
  void starburstPulse();
  void centerPulse();
  void rainbow();

  uint32_t getRandomColor();
  float getSpeed();
};

#endif // ANIMATIONCONTROLLER_H
