#include "Topology.h"

// Helper macros for internal use to match original data format
#define headof(S) Topology::headof(S)
#define tailof(S) Topology::tailof(S)

const int Topology::nodeConnections[Constants::NUMBER_OF_NODES][Constants::MAX_PATHS_PER_NODE] = {
    {-1, -1, 1, -1, 0, -1},
    {-1, -1, 3, -1, 2, -1},
    {-1, -1, 5, -1, 4, -1},
    {-1, 0, 6, 12, -1, -1},
    {-1, 2, 8, 14, 7, 1},

    {-1, 4, 10, 16, 9, 3},
    {-1, -1, -1, 18, 11, 5},
    {-1, 7, -1, 13, -1, 6},
    {-1, 9, -1, 15, -1, 8},
    {-1, 11, -1, 17, -1, 10},

    {12, -1, 19, -1, -1, -1},
    {14, -1, 21, -1, 20, -1},
    {16, -1, 23, -1, 22, -1},
    {18, -1, -1, -1, 24, -1},
    {13, 20, 25, 29, -1, 19},

    {15, 22, 27, 31, 26, 21},
    {17, 24, -1, 33, 28, 23},
    {-1, 26, -1, 30, -1, 25},
    {-1, 28, -1, 32, -1, 27},
    {29, -1, 34, -1, -1, -1},

    {31, -1, 36, -1, 35, -1},
    {33, -1, -1, -1, 37, -1},
    {30, 35, 38, -1, -1, 34},
    {32, 37, -1, -1, 39, 36},
    {-1, 39, -1, -1, -1, 38}};

const int Topology::segmentConnections[Constants::NUMBER_OF_SEGMENTS][Constants::SIDES_PER_SEGMENT] = {
    {0, 3},
    {0, 4},
    {1, 4},
    {1, 5},
    {2, 5},
    {2, 6},
    {3, 7},
    {4, 7},
    {4, 8},
    {5, 8},
    {5, 9},
    {6, 9}, // ayy
    {3, 10},
    {7, 14},
    {4, 11},
    {8, 15},
    {5, 12},
    {9, 16},
    {6, 13},
    {10, 14},
    {11, 14},
    {11, 15},
    {12, 15},
    {12, 16},
    {13, 16},
    {14, 17},
    {15, 17},
    {15, 18},
    {16, 18},
    {14, 19},
    {17, 22},
    {15, 20},
    {18, 23},
    {16, 21},
    {19, 22},
    {20, 22},
    {20, 23},
    {21, 23},
    {22, 24},
    {23, 24}};

const int Topology::ledAssignments[Constants::NUMBER_OF_SEGMENTS][3] = {
    {Constants::RED_INDEX, headof(3), tailof(3)},
    {Constants::RED_INDEX, tailof(2), headof(2)},
    {Constants::GREEN_INDEX, headof(10), tailof(10)},
    {Constants::GREEN_INDEX, tailof(9), headof(9)},
    {Constants::GREEN_INDEX, headof(4), tailof(4)},
    {Constants::GREEN_INDEX, tailof(3), headof(3)},

    {Constants::RED_INDEX, tailof(6), headof(6)},
    {Constants::BLACK_INDEX, tailof(11), headof(11)},
    {Constants::GREEN_INDEX, headof(11), tailof(11)},
    {Constants::GREEN_INDEX, tailof(8), headof(8)},
    {Constants::GREEN_INDEX, headof(12), tailof(12)},
    {Constants::BLUE_INDEX, tailof(11), headof(11)},

    {Constants::RED_INDEX, headof(4), tailof(4)},
    {Constants::BLACK_INDEX, tailof(10), headof(10)},
    {Constants::RED_INDEX, tailof(1), headof(1)},
    {Constants::GREEN_INDEX, tailof(7), headof(7)},
    {Constants::GREEN_INDEX, headof(5), tailof(5)},
    {Constants::BLUE_INDEX, tailof(10), headof(10)},
    {Constants::GREEN_INDEX, tailof(2), headof(2)},

    {Constants::RED_INDEX, headof(5), tailof(5)},
    {Constants::BLACK_INDEX, tailof(4), headof(4)},
    {Constants::BLACK_INDEX, headof(5), tailof(5)},
    {Constants::BLUE_INDEX, headof(5), tailof(5)},
    {Constants::BLUE_INDEX, tailof(4), headof(4)},
    {Constants::GREEN_INDEX, tailof(1), headof(1)},

    {Constants::BLACK_INDEX, tailof(9), headof(9)},
    {Constants::BLUE_INDEX, headof(6), tailof(6)},
    {Constants::GREEN_INDEX, tailof(6), headof(6)},
    {Constants::BLUE_INDEX, tailof(9), headof(9)},

    {Constants::BLACK_INDEX, tailof(3), headof(3)},
    {Constants::BLACK_INDEX, tailof(8), headof(8)},
    {Constants::BLACK_INDEX, headof(6), tailof(6)},
    {Constants::BLUE_INDEX, tailof(8), headof(8)},
    {Constants::BLUE_INDEX, tailof(3), headof(3)},

    {Constants::BLACK_INDEX, tailof(2), headof(2)},
    {Constants::BLACK_INDEX, headof(7), tailof(7)},
    {Constants::BLUE_INDEX, headof(7), tailof(7)},
    {Constants::BLUE_INDEX, tailof(2), headof(2)},

    {Constants::BLACK_INDEX, tailof(1), headof(1)},
    {Constants::BLUE_INDEX, tailof(1), headof(1)}};

const int Topology::borderNodes[Topology::numberOfBorderNodes] = {0, 1, 2, 3, 6, 10, 13, 19, 21, 24};

const int Topology::cubeNodes[Topology::numberOfCubeNodes] = {7, 8, 9, 11, 12, 17, 18, 20};

const int Topology::funNodes[Topology::numberOfFunNodes] = {4, 5, 14, 15, 16, 22, 23};

int Topology::getNextStep(int startNode, int targetNode)
{
  if (startNode == targetNode)
  {
    return -1;
  }
  if (startNode < 0 || startNode >= Constants::NUMBER_OF_NODES)
  {
    return -1;
  }
  if (targetNode < 0 || targetNode >= Constants::NUMBER_OF_NODES)
  {
    return -1;
  }

  int dist[Constants::NUMBER_OF_NODES];
  int parent[Constants::NUMBER_OF_NODES];
  for (int i = 0; i < Constants::NUMBER_OF_NODES; i++)
  {
    dist[i] = -1;
    parent[i] = -1;
  }

  int queue[Constants::NUMBER_OF_NODES];
  int front = 0;
  int rear = 0;

  queue[rear++] = targetNode;
  dist[targetNode] = 0;

  while (front < rear)
  {
    int u = queue[front++];

    if (u == startNode)
    {
      break;
    }

    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
      int segment = nodeConnections[u][i];
      if (segment != -1)
      {
        int v = (segmentConnections[segment][0] == u) ? segmentConnections[segment][1] : segmentConnections[segment][0];

        if (v >= 0 && v < Constants::NUMBER_OF_NODES && dist[v] == -1)
        {
          dist[v] = dist[u] + 1;
          parent[v] = u;
          queue[rear++] = v;
        }
      }
    }
  }

  int nextNode = parent[startNode];
  if (nextNode != -1)
  {
    for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
    {
      int segment = nodeConnections[startNode][i];
      if (segment != -1)
      {
        int v = (segmentConnections[segment][0] == startNode) ? segmentConnections[segment][1] : segmentConnections[segment][0];
        if (v == nextNode)
        {
          return i;
        }
      }
    }
  }

  return -1;
}
