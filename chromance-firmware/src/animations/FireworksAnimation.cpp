#include "FireworksAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

FireworksAnimation::FireworksAnimation(AnimationController &controller)
    : Animation(controller), launchRippleIndex(-1), targetNode(-1), exploding(false),
      lastKnownSegment(-1), lastKnownLed(-1), lastKnownNode(-1), lastKnownState(STATE_DEAD) {}

void FireworksAnimation::run()
{
    // Force kill all ripples to ensure a clean slate
    for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
    {
        controller.getRipple(i).state = STATE_DEAD;
    }

    exploding = false;
    launchRippleIndex = -1;
    lastKnownSegment = -1;

    int startNode = random(3);

    // Target higher nodes
    targetNode = 19 + random(6); // Nodes 19-24 are top nodes
    Ripple::runnerNode = targetNode;

    // Find a free ripple for the rocket
    for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
    {
        if (controller.getRipple(i).state == STATE_DEAD)
        {
            launchRippleIndex = i;
            break;
        }
    }

    if (launchRippleIndex >= 0)
    {
        // Find direction UP from selected start node
        int direction = 0;
        int bestY = -1; // Initialize with a very low value to find the highest Y
        for (int k = 0; k < Constants::MAX_PATHS_PER_NODE; k++)
        {
            int seg = Topology::nodeConnections[startNode][k];
            if (seg >= 0)
            {
                int other = (Topology::segmentConnections[seg][0] == startNode) ? Topology::segmentConnections[seg][1] : Topology::segmentConnections[seg][0];
                if (Topology::nodePositions[other].y > bestY)
                {
                    bestY = Topology::nodePositions[other].y;
                    direction = k;
                }
            }
        }

        // Set a random rocket duration, not dependent on path, to encourage mid-air explosions
        rocketDuration = 800 + random(800);

        // Start with long lifespan so we can control death in update()
        controller.getRipple(launchRippleIndex).start(startNode, direction,
                                                      0xFFFFFF, // White rocket
                                                      0.75f,    // Fast launch
                                                      10000,    // Safety margin
                                                      BEHAVIOR_CHASE);
    }
}

void FireworksAnimation::update()
{
    if (!exploding)
    {
        if (launchRippleIndex >= 0)
        {
            Ripple &r = controller.getRipple(launchRippleIndex);

            // Track position while alive
            if (r.state != STATE_DEAD)
            {
                lastKnownState = r.state;
                if (r.state == STATE_TRAVEL_UP || r.state == STATE_TRAVEL_DOWN)
                {
                    lastKnownSegment = r.node; // In travel state, node is segment
                    lastKnownLed = r.direction;
                    lastKnownNode = -1;
                }
                else if (r.state == STATE_WITHIN_NODE)
                {
                    lastKnownNode = r.node;
                    lastKnownSegment = -1;
                }
            }

            bool timeUp = (millis() - r.birthday >= rocketDuration);
            bool reachedTarget = (r.state != STATE_DEAD && r.state == STATE_WITHIN_NODE && r.node == targetNode);
            bool isFalling = (r.state == STATE_TRAVEL_DOWN);
            bool dead = (r.state == STATE_DEAD);

            if (timeUp || reachedTarget || isFalling || dead)
            {
                exploding = true;

                int explodeNode = -1;
                int explodeSeg = -1;
                int explodeLed = -1;

                // Capture position from live ripple if possible
                if (!dead)
                {
                    if (r.state == STATE_WITHIN_NODE)
                    {
                        explodeNode = r.node;
                    }
                    else if (r.state == STATE_TRAVEL_UP || r.state == STATE_TRAVEL_DOWN)
                    {
                        if (isFalling && r.node >= 0 && r.node < Constants::NUMBER_OF_SEGMENTS)
                        {
                            // Falling from apex (Side 0)
                            explodeNode = Topology::segmentConnections[r.node][0];
                        }
                        else
                        {
                            // Mid-air explosion (time out)
                            explodeSeg = r.node;
                            explodeLed = r.direction;
                        }
                    }
                }
                else
                {
                    // Fallback to last known if it died unexpectedly
                    if (lastKnownNode != -1)
                        explodeNode = lastKnownNode;
                    else
                    {
                        explodeSeg = lastKnownSegment;
                        explodeLed = lastKnownLed;
                    }
                }

                // Kill the rocket
                if (r.state != STATE_DEAD)
                    r.state = STATE_DEAD;
                launchRippleIndex = -1;

                uint32_t color = controller.getRandomColor();

                if (explodeSeg != -1)
                {
                    // Mid-segment explosion
                    int found = 0;
                    for (int i = 0; i < Constants::NUMBER_OF_RIPPLES && found < 2; i++)
                    {
                        Ripple &part = controller.getRipple(i);
                        if (part.state == STATE_DEAD)
                        {
                            part.color = color;
                            part.speed = 0.5f;
                            part.lifespan = 800 + random(600);
                            part.behavior = BEHAVIOR_FEISTY;
                            part.birthday = millis();
                            part.state = (found == 0) ? STATE_TRAVEL_UP : STATE_TRAVEL_DOWN;
                            part.node = explodeSeg;
                            part.direction = explodeLed;
                            found++;
                        }
                    }
                }
                else if (explodeNode != -1)
                {
                    // Node explosion: Collect valid directions
                    int validDirs[Constants::MAX_PATHS_PER_NODE];
                    int validCount = 0;
                    for (int k = 0; k < Constants::MAX_PATHS_PER_NODE; k++)
                    {
                        if (Topology::nodeConnections[explodeNode][k] >= 0)
                        {
                            validDirs[validCount++] = k;
                        }
                    }

                    // Shuffle valid directions to ensure randomness
                    for (int k = 0; k < validCount; k++)
                    {
                        int r = random(validCount);
                        int temp = validDirs[k];
                        validDirs[k] = validDirs[r];
                        validDirs[r] = temp;
                    }

                    // Spawn a random number of particles (1 to min(4, validCount))
                    int num_particles_to_spawn = random(1, (validCount < 4 ? validCount : 4) + 1);
                    int spawned = 0;
                    for (int k = 0; k < num_particles_to_spawn; k++)
                    {
                        int dir = validDirs[k];
                        controller.startRipple(
                            explodeNode,
                            dir,
                            color,
                            0.5f,
                            1000 + random(600),
                            BEHAVIOR_FEISTY);
                        spawned++;
                    }
                }
            }
        }
        else
        {
            // Rocket lost? Try to restart occasionally
            if (random(100) < 5)
                run();
        }
    }
    else
    {
        // Wait for explosion to fade before next launch
        if (controller.getActiveRippleCount() < 2)
        {
            if (random(100) < 15)
                run();
        }
    }
}