#include "ChaseAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

void ChaseAnimation::run()
{
  int runnerStartNode = random(Constants::NUMBER_OF_NODES);
  int chaserStartNode = random(Constants::NUMBER_OF_NODES);

  // Ensure they are different
  while (chaserStartNode == runnerStartNode)
  {
    chaserStartNode = random(Constants::NUMBER_OF_NODES);
  }

  // Pick valid start directions
  int runnerDirection = -1;
  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    if (Topology::nodeConnections[runnerStartNode][i] >= 0)
    {
      runnerDirection = i;
      if (random(2) == 0)
        break; // Randomize start direction slightly
    }
  }

  int chaserDirection = -1;
  for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
  {
    if (Topology::nodeConnections[chaserStartNode][i] >= 0)
    {
      chaserDirection = i;
      if (random(2) == 0)
        break;
    }
  }

  if (runnerDirection != -1 && chaserDirection != -1)
  {
    // Blue dot (runner)
    controller.startRipple(
        runnerStartNode,
        runnerDirection,
        0x0000FF, // Blue
        1.0f,     // Speed
        20000,    // Lifespan 20s
        BEHAVIOR_RUNNER);

    // Yellow dot (chaser)
    controller.startRipple(
        chaserStartNode,
        chaserDirection,
        0xFFFF00, // Yellow
        1.1f,     // Slightly faster
        20000,    // Lifespan 20s
        BEHAVIOR_CHASE);
  }
}

void ChaseAnimation::update()
{
  int runnerIndex = -1;
  int chaserIndex = -1;

  // Find the runner and chaser ripples
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    Ripple &r = controller.getRipple(i);
    if (r.state != STATE_DEAD)
    {
      // We have to inspect private members of Ripple?
      // Ripple members are public in Ripple.h
      if (r.getBehavior() == BEHAVIOR_RUNNER)
      {
        runnerIndex = i;
      }
      else if (r.getBehavior() == BEHAVIOR_CHASE)
      {
        chaserIndex = i;
      }
    }
  }

  if (runnerIndex != -1 && chaserIndex != -1)
  {
    Ripple &runner = controller.getRipple(runnerIndex);
    Ripple &chaser = controller.getRipple(chaserIndex);

    bool collision = false;
    int collisionNode = -1;

    // Check for collision
    // Case 1: Both in same node
    if (runner.state == STATE_WITHIN_NODE && chaser.state == STATE_WITHIN_NODE)
    {
      if (runner.node == chaser.node)
      {
        collision = true;
        collisionNode = runner.node;
      }
    }
    // Case 2: Both on same segment
    else if ((runner.state == STATE_TRAVEL_UP || runner.state == STATE_TRAVEL_DOWN) &&
             (chaser.state == STATE_TRAVEL_UP || chaser.state == STATE_TRAVEL_DOWN))
    {
      // For traveling ripples, 'node' represents the segment index
      if (runner.node == chaser.node)
      {
        // On same segment. Are they close?
        // For now, let's assume if they are on the same segment, it's a catch.
        // Or maybe we should wait for them to pass each other?
        // If one is fast and one is slow, they might just be on same segment.
        // But simplified logic: same segment = caught.
        collision = true;

        // Determine collision node for explosion (closest node)
        // Just pick one of the connected nodes
        if (runner.node >= 0 && runner.node < Constants::NUMBER_OF_SEGMENTS)
        {
          // Get a node connected to this segment
          collisionNode = Topology::segmentConnections[runner.node][0];
        }
      }
    }
    // Case 3: One in node, one in segment connected to that node?
    // Let's stick to strict same-location checks for now to avoid false positives.

    if (collision)
    {
      // Kill both
      runner.state = STATE_DEAD;
      chaser.state = STATE_DEAD;

      // Explosion!
      if (collisionNode >= 0)
      {
        for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
        {
          if (Topology::nodeConnections[collisionNode][i] >= 0)
          {
            controller.startRipple(
                collisionNode,
                i,
                0xFF0000, // Red explosion
                2.5f,
                2000,
                BEHAVIOR_EXPLODING // Or random
            );
          }
        }
      }
    }
  }
}

void ChaseAnimation::stop()
{
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    Ripple &r = controller.getRipple(i);
    if (r.state != STATE_DEAD)
    {
      if (r.getBehavior() == BEHAVIOR_RUNNER || r.getBehavior() == BEHAVIOR_CHASE)
      {
        r.state = STATE_DEAD;
      }
    }
  }
}

bool ChaseAnimation::isFinished()
{
  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    Ripple &r = controller.getRipple(i);
    if (r.state != STATE_DEAD)
    {
      RippleBehavior b = r.getBehavior();
      if (b == BEHAVIOR_RUNNER || b == BEHAVIOR_CHASE)
      {
        return false;
      }
    }
  }
  return true;
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(ChaseAnimation)
