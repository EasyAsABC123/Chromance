#include "AnimationController.h"

AnimationController::AnimationController(LedController &controller)
    : ledController(controller)
{
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    ripples[i] = Ripple(i);
  }
}

void AnimationController::init()
{
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
  switch (animation)
  {
  case 0:
    randomPulse();
    break;
  case 1:
    cubePulse();
    break;
  case 2:
    starburstPulse();
    break;
  case 3:
    centerPulse();
    break;
  case 4:
    rainbow();
    break;
  default:
    break;
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

void AnimationController::randomPulse()
{
  int node = Topology::funNodes[random(Topology::numberOfFunNodes)];
  while (node == lastAutoPulseNode)
  {
    node = Topology::funNodes[random(Topology::numberOfFunNodes)];
  }
  lastAutoPulseNode = node;

  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    if (Topology::nodeConnections[node][i] >= 0)
    {
      for (int j = 0; j < Constants::NUMBER_OF_RIPPLES; j++)
      {
        if (ripples[j].state == STATE_DEAD)
        {
          ripples[j].start(
              node,
              i,
              getRandomColor(),
              float(random(100)) / 100.0f * .2f + .5f,
              Constants::ANIMATION_TIME,
              BEHAVIOR_FEISTY);
          break;
        }
      }
    }
  }
}

void AnimationController::cubePulse()
{
  int node = Topology::cubeNodes[random(Topology::numberOfCubeNodes)];
  while (node == lastAutoPulseNode)
  {
    node = Topology::cubeNodes[random(Topology::numberOfCubeNodes)];
  }
  lastAutoPulseNode = node;

  RippleBehavior behavior = random(2) ? BEHAVIOR_ALWAYS_LEFT : BEHAVIOR_ALWAYS_RIGHT;

  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    if (Topology::nodeConnections[node][i] >= 0)
    {
      for (int j = 0; j < Constants::NUMBER_OF_RIPPLES; j++)
      {
        if (ripples[j].state == STATE_DEAD)
        {
          ripples[j].start(
              node,
              i,
              getRandomColor(),
              .8f,
              Constants::ANIMATION_TIME,
              behavior);
          break;
        }
      }
    }
  }
}

void AnimationController::starburstPulse()
{
  RippleBehavior behavior = random(2) ? BEHAVIOR_ALWAYS_LEFT : BEHAVIOR_ALWAYS_RIGHT;
  lastAutoPulseNode = Topology::starburstNode;

  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    for (int j = 0; j < Constants::NUMBER_OF_RIPPLES; j++)
    {
      if (ripples[j].state == STATE_DEAD)
      {
        // strip0.ColorHSV(baseColor + (0xFFFF / 6) * i, 255, 255)
        uint32_t color = ledController.ColorHSV(baseColor + (0xFFFF / 6) * i, 255, 255);

        ripples[j].start(
            Topology::starburstNode,
            i,
            color,
            .65f,
            2600,
            behavior);
        break;
      }
    }
  }
}

void AnimationController::centerPulse()
{
  unsigned int startingNode = Topology::starburstNode;
  RippleBehavior behavior = BEHAVIOR_FEISTY;

  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    if (Topology::nodeConnections[startingNode][i] >= 0)
    {
      for (int j = 0; j < Constants::NUMBER_OF_RIPPLES; j++)
      {
        if (ripples[j].state == STATE_DEAD)
        {
          ripples[j].start(
              startingNode,
              i,
              getRandomColor(),
              getSpeed(),
              5000,
              behavior);
          break;
        }
      }
    }
  }
}

void AnimationController::rainbow()
{
  ledController.rainbow();
}
