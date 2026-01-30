#include "AnimationController.h"
#include "animations/RandomAnimation.h"
#include "animations/CubeAnimation.h"
#include "animations/StarburstAnimation.h"
#include "animations/CenterAnimation.h"
#include "animations/RainbowAnimation.h"
#include "animations/ChaseAnimation.h"
#include "animations/HeartbeatAnimation.h"
#include "animations/RainbowPinwheelAnimation.h"
#include "animations/RainbowRadiateAnimation.h"
#include "animations/ShootingStarAnimation.h"
#include "animations/MeteorShowerAnimation.h"
#include "animations/SearchlightAnimation.h"
#include "animations/BioPulseAnimation.h"
#include "animations/GlitchAnimation.h"
#include "animations/WaterAnimation.h"
#include "animations/InfernoAnimation.h"
#include "animations/BouncingBallsAnimation.h"
#include "animations/FirefliesAnimation.h"
#include "animations/FireworksAnimation.h"

AnimationController::AnimationController(LedController &controller, Configuration &config)
    : ledController(controller), configuration(config)
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

void AnimationController::recalculateAutoPulseTypes()
{
  numberOfAutoPulseTypes = 0;
  for (int i = 0; i < Constants::NUMBER_OF_ANIMATIONS; i++)
  {
    if (animations[i] != nullptr && animations[i]->isEnabled())
    {
      numberOfAutoPulseTypes++;
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
    animations[5] = new ChaseAnimation(*this);
    animations[6] = new HeartbeatAnimation(*this);
    animations[7] = new RainbowPinwheelAnimation(*this);
    animations[8] = new RainbowRadiateAnimation(*this);
    animations[9] = new ShootingStarAnimation(*this);
    animations[10] = new MeteorShowerAnimation(*this);
    animations[11] = new SearchlightAnimation(*this);
    animations[12] = new BioPulseAnimation(*this);
    animations[13] = new GlitchAnimation(*this);
    animations[14] = new WaterAnimation(*this);
    animations[15] = new InfernoAnimation(*this);
    animations[16] = new BouncingBallsAnimation(*this);
    animations[17] = new FirefliesAnimation(*this);
    animations[18] = new FireworksAnimation(*this);
  }

  recalculateAutoPulseTypes();

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

  // Update current animation
  if (currentAutoPulseType < Constants::NUMBER_OF_ANIMATIONS && animations[currentAutoPulseType])
  {
    animations[currentAutoPulseType]->update();
  }

  // Check for new animation trigger
  if (numberOfAutoPulseTypes > 0 && millis() - lastRandomPulse >= Constants::randomPulseTime)
  {
    bool readyToSwitch = true;

    if (currentAutoPulseType < Constants::NUMBER_OF_ANIMATIONS && animations[currentAutoPulseType])
    {
      if (!animations[currentAutoPulseType]->canBePreempted() && !animations[currentAutoPulseType]->isFinished())
      {
        readyToSwitch = false;
      }
    }

    if (readyToSwitch)
    {
      if (autoSwitching)
      {
        if (currentAutoPulseType < Constants::NUMBER_OF_ANIMATIONS && animations[currentAutoPulseType])
        {
          animations[currentAutoPulseType]->stop();
        }

        baseColor = random(0xFFFF);

        getNextAnimation();
        startAnimation(currentAutoPulseType);

        lastRandomPulse = millis();
      }
      else
      {
        // Manual mode: continue playing selected animation
        // Only re-trigger if the animation considers itself finished (e.g. one-shot pulses)
        if (currentAutoPulseType < Constants::NUMBER_OF_ANIMATIONS && animations[currentAutoPulseType] && animations[currentAutoPulseType]->isFinished())
        {
          // We don't stop(), just add another pulse/run
          // For ChaseAnimation, we might want to be careful, but isFinished() should handle that.
          // For Random/Cube/etc, isFinished() is true, so we add more ripples.
          rollNewBaseColor();  // New random color for each re-triggered pulse in manual mode (differs from previous)
          animations[currentAutoPulseType]->run();
          lastRandomPulse = millis();
        }
      }
    }
  }
}

void AnimationController::rollNewBaseColor()
{
  unsigned int prev = baseColor;
  int attempts = 0;
  do {
    baseColor = random(0xFFFF);
  } while (baseColor == prev && attempts++ < 16);
  if (baseColor == prev)
    baseColor = (prev + 0x8000) & 0xFFFF;  // Fallback: opposite hue so it always differs
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
      possiblePulse = random(Constants::NUMBER_OF_ANIMATIONS); // 0 to NUMBER_OF_ANIMATIONS-1

      if (possiblePulse == currentAutoPulseType)
      {
        attempts++;
        continue;
      }

      if (animations[possiblePulse] != nullptr && animations[possiblePulse]->isEnabled())
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
  currentAutoPulseType = animation;
  if (animation < Constants::NUMBER_OF_ANIMATIONS && animations[animation])
  {
    animations[animation]->run();
  }
  notifyStateChange();
}

void AnimationController::changeAnimation(byte animation)
{
  if (currentAutoPulseType < Constants::NUMBER_OF_ANIMATIONS && animations[currentAutoPulseType])
  {
    animations[currentAutoPulseType]->stop();
  }
  rollNewBaseColor();  // New random color when manually selecting (differs from previous)
  startAnimation(animation);
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

int AnimationController::getActiveRippleCount() const
{
  int count = 0;
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    if (ripples[i].state != STATE_DEAD)
    {
      count++;
    }
  }
  return count;
}

void AnimationController::setAutoSwitching(bool enabled)
{
  autoSwitching = enabled;
  notifyStateChange();
}

Ripple &AnimationController::getRipple(int index)
{
  if (index < 0 || index >= Constants::NUMBER_OF_RIPPLES)
  {
    // Return the first one as a fallback or handle error?
    // For now we assume valid index or return 0
    return ripples[0];
  }
  return ripples[index];
}

Animation *AnimationController::getAnimation(int index)
{
  if (index < 0 || index >= Constants::NUMBER_OF_ANIMATIONS)
  {
    return nullptr;
  }
  return animations[index];
}

void AnimationController::notifyStateChange()
{
  if (stateChangeCallback)
  {
    stateChangeCallback(currentAutoPulseType, autoSwitching);
  }
}
