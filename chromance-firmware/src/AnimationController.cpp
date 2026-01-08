#include "AnimationController.h"
#include "animations/RandomAnimation.h"
#include "animations/CubeAnimation.h"
#include "animations/StarburstAnimation.h"
#include "animations/CenterAnimation.h"
#include "animations/RainbowAnimation.h"

AnimationController::AnimationController(LedController &controller)
    : ledController(controller)
{
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    ripples[i] = Ripple(i);
  }

  for (int i = 0; i < Constants::NUMBER_OF_ANIMATIONS; i++)
  {
    animations[i] = nullptr;
  }
}

AnimationController::~AnimationController()
{
  for (int i = 0; i < Constants::NUMBER_OF_ANIMATIONS; i++)
  {
    if (animations[i] != nullptr)
    {
      delete animations[i];
      animations[i] = nullptr;
    }
  }
}

void AnimationController::init()
{
  if (animations[0] == nullptr)
  {
    animations[0] = new RandomAnimation(*this);
    animations[1] = new CubeAnimation(*this);
    animations[2] = new StarburstAnimation(*this);
    animations[3] = new CenterAnimation(*this);
    animations[4] = new RainbowAnimation(*this);
  }

  numberOfAutoPulseTypes =
      (Constants::randomPulsesEnabled ? 1 : 0) +
      (Constants::cubePulsesEnabled ? 1 : 0) +
      (Constants::starburstPulsesEnabled ? 1 : 0) +
      (Constants::centerPulseEnabled ? 1 : 0) +
      (Constants::rainbowEnabled ? 1 : 0);

  baseColor = random(0xFFFF);
  lastRandomPulse = millis();
}

void AnimationController::update()
{
  // Fade all dots to create trails
  // In main.cpp: fade() -> ledController.fade(decay)
  // Global 'decay' was 0.97 in variables.cpp
  // We should move decay to Constants or AnimationController
  // I'll use a local constant or member
  float decay = 0.97f; // TODO: Move to Constants if needed
  ledController.fade(decay);

  // Advance ripples
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    ripples[i].advance(ledController);
  }

  // Show strips
  ledController.show();

  // Check for new animation trigger
  if (numberOfAutoPulseTypes > 0 && millis() - lastRandomPulse >= Constants::randomPulseTime)
  {
    baseColor = random(0xFFFF);

    getNextAnimation();
    startAnimation(currentAutoPulseType);

    lastRandomPulse = millis();
  }
}

void AnimationController::getNextAnimation()
{
  if (currentAutoPulseType == 255 || (numberOfAutoPulseTypes > 1 && millis() - lastAutoPulseChange >= Constants::RIPPLE_TIMEOUT))
  {
    byte possiblePulse = 255;

    // Safety counter to prevent infinite loop if nothing enabled (though numberOfAutoPulseTypes check handles that)
    int attempts = 0;
    while (attempts < 100)
    {
      possiblePulse = random(5); // 0 to 4

      if (possiblePulse == currentAutoPulseType)
      {
        attempts++;
        continue;
      }

      bool accepted = false;
      switch (possiblePulse)
      {
      case 0:
        accepted = Constants::randomPulsesEnabled;
        break;
      case 1:
        accepted = Constants::cubePulsesEnabled;
        break;
      case 2:
        accepted = Constants::starburstPulsesEnabled;
        break;
      case 3:
        accepted = Constants::centerPulseEnabled;
        break;
      case 4:
        accepted = Constants::rainbowEnabled;
        break;
      }

      if (accepted)
      {
        currentAutoPulseType = possiblePulse;
        lastAutoPulseChange = millis();
        break;
      }
      attempts++;
    }
  }
}

void AnimationController::startAnimation(byte animation)
{
  if (animation < 5 && animations[animation])
  {
    animations[animation]->run();
  }
}

uint32_t AnimationController::getRandomColor()
{
  return ledController.ColorHSV(baseColor, 255, 255);
}

float AnimationController::getSpeed()
{
  return random(500, 800) / 1000.0f;
}

void AnimationController::startRipple(int node, int direction, uint32_t color, float speed, unsigned long lifespan, RippleBehavior behavior)
{
  for (int j = 0; j < Constants::NUMBER_OF_RIPPLES; j++)
  {
    if (ripples[j].state == STATE_DEAD)
    {
      ripples[j].start(
          node,
          direction,
          color,
          speed,
          lifespan,
          behavior);
      break;
    }
  }
}

byte AnimationController::getLastNode()
{
  return lastAutoPulseNode;
}

void AnimationController::setLastNode(byte node)
{
  lastAutoPulseNode = node;
}

LedController &AnimationController::getLedController()
{
  return ledController;
}

unsigned int AnimationController::getBaseColor()
{
  return baseColor;
}
