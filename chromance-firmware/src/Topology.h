#ifndef TOPOLOGY_H
#define TOPOLOGY_H

#include "Constants.h"

class Topology
{
public:
  static constexpr int headof(int s)
  {
    return (s - 1) * Constants::LEDS_PER_SEGMENT;
  }

  static constexpr int tailof(int s)
  {
    return headof(s) + (Constants::LEDS_PER_SEGMENT - 1);
  }

  // Node connections: [Node][PathIndex] -> Connected Segment ID
  static const int nodeConnections[Constants::NUMBER_OF_NODES][Constants::MAX_PATHS_PER_NODE];

  // Segment connections: [Segment][Side] -> Connected Node ID
  // Side 0: Closer to ceiling, Side 1: Closer to floor
  static const int segmentConnections[Constants::NUMBER_OF_SEGMENTS][Constants::SIDES_PER_SEGMENT];

  // LED Assignments: [Segment][3] -> {StripIndex, CeilingLedIndex, FloorLedIndex}
  static const int ledAssignments[Constants::NUMBER_OF_SEGMENTS][3];

  static const int numberOfBorderNodes = 10;
  static const int borderNodes[numberOfBorderNodes];

  static const int numberOfCubeNodes = 8;
  static const int cubeNodes[numberOfCubeNodes];

  static const int numberOfFunNodes = 7;
  static const int funNodes[numberOfFunNodes];

  static const int starburstNode = 15;
};

#endif // TOPOLOGY_H
