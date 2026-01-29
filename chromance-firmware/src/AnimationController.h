#ifndef ANIMATIONCONTROLLER_H
#define ANIMATIONCONTROLLER_H

#include <Arduino.h>
#include "Constants.h"
#include "LedController.h"
#include "Configuration.h"
#include "ripple.h"
#include "Topology.h"
#include <functional>

class Animation;

class AnimationController
{
public:
  using StateChangeCallback = std::function<void(byte currentAnimation, bool autoSwitching)>;

  AnimationController(LedController &ledController, Configuration &configuration);
  ~AnimationController();
  void init();
  void update(); // Main loop update (advance animations)

  // Helper methods exposed for animations
  void startRipple(int node, int direction, uint32_t color, float speed, unsigned long lifespan, RippleBehavior behavior);
  uint32_t getRandomColor();
  float getSpeed();
  byte getLastNode();
  void setLastNode(byte node);
  LedController &getLedController();
  Configuration &getConfiguration() { return configuration; }
  unsigned int getBaseColor();
  int getActiveRippleCount() const;
  byte getCurrentAnimation() const { return currentAutoPulseType; }
  void startAnimation(byte animation);
  void changeAnimation(byte animation);
  void setAutoSwitching(bool enabled);
  bool isAutoSwitching() const { return autoSwitching; }
  Ripple &getRipple(int index);
  Animation *getAnimation(int index);
  void setStateChangeCallback(StateChangeCallback callback) { stateChangeCallback = callback; }
  void recalculateAutoPulseTypes();

private:
  LedController &ledController;
  Configuration &configuration;
  Ripple ripples[Constants::NUMBER_OF_RIPPLES];
  class Animation *animations[Constants::NUMBER_OF_ANIMATIONS];

  unsigned int baseColor;
  unsigned long lastRandomPulse;
  bool autoSwitching = true;

  byte currentAutoPulseType = 255;
  unsigned long lastAutoPulseChange;
  byte lastAutoPulseNode = 255;

  // Auto pulse types count
  byte numberOfAutoPulseTypes;

  StateChangeCallback stateChangeCallback;

  void getNextAnimation();
  void notifyStateChange();
  void rollNewBaseColor();  // Picks a new random baseColor different from the previous
};

#endif // ANIMATIONCONTROLLER_H
