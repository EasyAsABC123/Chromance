#ifndef RIPPLE_H_
#define RIPPLE_H_

#include <Arduino.h>
#include "Constants.h"
#include "Topology.h"
#include "LedController.h"

// Define ripple behaviors
enum RippleState
{
  STATE_DEAD,        // Ripple is to be deleted and should not lit up
  STATE_WITHIN_NODE, // Ripple isn't drawn as it passes through a node to keep the speed consistent
  STATE_TRAVEL_UP,   // Ripple is moving upward
  STATE_TRAVEL_DOWN  // Ripple is moving downward
};

enum RippleBehavior
{
  BEHAVIOR_COUCH_POTATO, // Stop at next node
  BEHAVIOR_LAZY,         // Only go straight
  BEHAVIOR_WEAK,         // Go straight if possible
  BEHAVIOR_FEISTY,
  BEHAVIOR_ANGRY,
  BEHAVIOR_ALWAYS_RIGHT,
  BEHAVIOR_ALWAYS_LEFT,
  BEHAVIOR_EXPLODING
};

class Ripple
{
public:
  Ripple(int id = 0); // Default constructor with default ID

  void start(int node, int direction, unsigned long color, float speed, unsigned long lifespan, RippleBehavior behavior);
  void advance(LedController &ledController);

  RippleState state = STATE_DEAD;
  unsigned long color;

  /*
  If within a node: 0 is node, 1 is direction
  If traveling, 0 is segment, 1 is LED position from bottom
  */
  int node;
  int direction;

private:
  void renderLed(LedController &ledController, unsigned long age);

  float speed;            // Each loop, ripples move this many LED's.
  unsigned long lifespan; // The ripple stops after this many milliseconds
  RippleBehavior behavior;
  bool justStarted = false;
  float pressure;         // When Pressure reaches 1, ripple will move
  unsigned long birthday; // Used to track age of ripple

  // static byte rippleCount; // Unused?
  byte rippleId; // Used to identify this ripple in debug output
};

#endif
