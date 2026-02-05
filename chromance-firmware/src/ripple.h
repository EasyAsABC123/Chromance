#ifndef RIPPLE_H_
#define RIPPLE_H_

#include <Arduino.h>
#include "Constants.h"
#include "Topology.h"
#include "LedController.h"

// Define ripple behaviors
enum RippleBehavior
{
  BEHAVIOR_COUCH_POTATO, // Stop at next node
  BEHAVIOR_LAZY,         // Only go straight
  BEHAVIOR_WEAK,         // Go straight if possible
  BEHAVIOR_FEISTY,
  BEHAVIOR_ANGRY,
  BEHAVIOR_ALWAYS_RIGHT,
  BEHAVIOR_ALWAYS_LEFT,
  BEHAVIOR_EXPLODING,
  BEHAVIOR_CHASE,
  BEHAVIOR_RUNNER
};

enum RippleState
{
  STATE_DEAD,
  STATE_WITHIN_NODE,
  STATE_TRAVEL_UP,
  STATE_TRAVEL_DOWN
};

class Ripple
{
public:
  Ripple(int id = 0); // Default constructor with default ID

  void start(int node, int direction, unsigned long color, float speed, unsigned long lifespan, RippleBehavior behavior);
  void advance(LedController &ledController);
  RippleBehavior getBehavior() const { return behavior; }

  RippleState state = STATE_DEAD;
  unsigned long color;

  /*
  If within a node: 0 is node, 1 is direction
  If traveling, 0 is segment, 1 is LED position from bottom
  */
  int node;
  int direction;

  static int runnerNode;
  int targetNode = -1;

  float speed;            // Each loop, ripples move this many LED's.
  unsigned long lifespan; // The ripple stops after this many milliseconds
  RippleBehavior behavior;
  unsigned long birthday; // Used to track age of ripple

private:
  void renderLed(LedController &ledController, unsigned long age);

  bool justStarted = false;
  float pressure;         // When Pressure reaches 1, ripple will move

  // static byte rippleCount; // Unused?
  byte rippleId; // Used to identify this ripple in debug output
};

#endif
