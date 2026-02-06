#include "FireworksAnimation.h"
#include "../AnimationController.h"
#include "../Topology.h"
#include "../Constants.h"

FireworksAnimation::FireworksAnimation(AnimationController &controller)
    : Animation(controller)
{
    for (int i = 0; i < MAX_FIREWORKS; i++)
    {
        fireworks[i].active = false;
        fireworks[i].rippleIndex = -1;
    }
}

bool FireworksAnimation::canBePreempted()
{
    for (int i = 0; i < MAX_FIREWORKS; i++)
    {
        if (fireworks[i].active)
            return false;
    }
    return true;
}

bool FireworksAnimation::isFinished()
{
    return false;
}

void FireworksAnimation::run()
{
    // Clear state
    for (int i = 0; i < MAX_FIREWORKS; i++)
    {
        fireworks[i].active = false;
        fireworks[i].rippleIndex = -1;
    }

    // Launch the first one immediately
    launchFirework();
}

void FireworksAnimation::launchFirework()
{
    // Find a free slot
    int slot = -1;
    for (int i = 0; i < MAX_FIREWORKS; i++)
    {
        if (!fireworks[i].active)
        {
            slot = i;
            break;
        }
    }

    if (slot == -1)
        return;

    // Find a free ripple
    int rippleIndex = -1;
    for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
    {
        if (controller.getRipple(i).state == STATE_DEAD)
        {
            rippleIndex = i;
            break;
        }
    }

    if (rippleIndex == -1)
        return;

    // Setup launch parameters
    int startNode = 24;         // Bottom
    int targetNode = random(3); // Top nodes 0-2

    int validDirs[Constants::MAX_PATHS_PER_NODE];
    int validCount = 0;

    for (int k = 0; k < Constants::MAX_PATHS_PER_NODE; k++)
    {
        int seg = Topology::nodeConnections[startNode][k];
        if (seg >= 0)
        {
            int other = (Topology::segmentConnections[seg][0] == startNode) ? Topology::segmentConnections[seg][1] : Topology::segmentConnections[seg][0];
            if (Topology::nodePositions[other].y < Topology::nodePositions[startNode].y)
            {
                validDirs[validCount++] = k;
            }
        }
    }

    int direction = 0;
    if (validCount > 0)
    {
        direction = validDirs[random(validCount)];
    }

    int minDuration = 1000;
    int maxDuration = 4000;
    unsigned long duration = minDuration + random(maxDuration - minDuration);

    controller.getRipple(rippleIndex).start(startNode, direction, 0xFFFFFF, 0.75f, 10000, BEHAVIOR_RUNNER);
    controller.getRipple(rippleIndex).targetNode = targetNode;

    fireworks[slot].active = true;
    fireworks[slot].rippleIndex = rippleIndex;
    fireworks[slot].targetNode = targetNode;
    fireworks[slot].duration = duration;
    fireworks[slot].lastKnownSegment = -1;
    fireworks[slot].lastKnownLed = -1;
    fireworks[slot].lastKnownNode = -1;
}

void FireworksAnimation::update()
{
    // 1. Manage active fireworks
    for (int i = 0; i < MAX_FIREWORKS; i++)
    {
        if (!fireworks[i].active)
            continue;

        Ripple &r = controller.getRipple(fireworks[i].rippleIndex);

        // Track position
        if (r.state != STATE_DEAD)
        {
            if (r.state == STATE_TRAVEL_UP || r.state == STATE_TRAVEL_DOWN)
            {
                fireworks[i].lastKnownSegment = r.node;
                fireworks[i].lastKnownLed = r.direction;
                fireworks[i].lastKnownNode = -1;
            }
            else if (r.state == STATE_WITHIN_NODE)
            {
                fireworks[i].lastKnownNode = r.node;
                fireworks[i].lastKnownSegment = -1;
            }
        }

        bool timeUp = (millis() - r.birthday >= fireworks[i].duration);
        bool reachedTarget = (r.state != STATE_DEAD && r.state == STATE_WITHIN_NODE && r.node == fireworks[i].targetNode);
        bool isFalling = (r.state == STATE_TRAVEL_DOWN);
        bool dead = (r.state == STATE_DEAD);

        if (timeUp || reachedTarget || isFalling || dead)
        {
            explodeFirework(i);
        }
    }

    // 2. Chance to launch new firework
    // Higher chance if fewer active rockets
    int activeCount = 0;
    for (int i = 0; i < MAX_FIREWORKS; i++)
    {
        if (fireworks[i].active)
            activeCount++;
    }

    if (activeCount < MAX_FIREWORKS)
    {
        // 2% chance per frame to launch another
        if (random(100) < 2)
        {
            launchFirework();
        }
    }
}

void FireworksAnimation::explodeFirework(int index)
{
    if (!fireworks[index].active)
        return;

    Ripple &r = controller.getRipple(fireworks[index].rippleIndex);

    int explodeNode = -1;
    int explodeSeg = -1;
    int explodeLed = -1;

    // Capture position
    if (r.state != STATE_DEAD)
    {
        if (r.state == STATE_WITHIN_NODE)
        {
            explodeNode = r.node;
        }
        else if (r.state == STATE_TRAVEL_UP || r.state == STATE_TRAVEL_DOWN)
        {
            if (r.state == STATE_TRAVEL_DOWN && r.node >= 0 && r.node < Constants::NUMBER_OF_SEGMENTS)
            {
                explodeNode = Topology::segmentConnections[r.node][0];
            }
            else
            {
                explodeSeg = r.node;
                explodeLed = r.direction;
            }
        }
    }
    else
    {
        // Fallback
        if (fireworks[index].lastKnownNode != -1)
            explodeNode = fireworks[index].lastKnownNode;
        else
        {
            explodeSeg = fireworks[index].lastKnownSegment;
            explodeLed = fireworks[index].lastKnownLed;
        }
    }

    // Kill rocket
    if (r.state != STATE_DEAD)
        r.state = STATE_DEAD;

    // Mark slot inactive
    fireworks[index].active = false;
    fireworks[index].rippleIndex = -1;

    // Spawn explosion
    uint32_t color = controller.getLedController().ColorHSV(random(65535), 255, 255);

    if (explodeSeg != -1)
    {
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
                part.targetNode = -1; // Reset target
                found++;
            }
        }
    }
    else if (explodeNode != -1)
    {
        int validDirs[Constants::MAX_PATHS_PER_NODE];
        int validCount = 0;
        for (int k = 0; k < Constants::MAX_PATHS_PER_NODE; k++)
        {
            if (Topology::nodeConnections[explodeNode][k] >= 0)
            {
                validDirs[validCount++] = k;
            }
        }

        for (int k = 0; k < validCount; k++)
        {
            int r = random(validCount);
            int temp = validDirs[k];
            validDirs[k] = validDirs[r];
            validDirs[r] = temp;
        }

        int num_particles = random(1, (validCount < 4 ? validCount : 4) + 1);
        for (int k = 0; k < num_particles; k++)
        {
            int dir = validDirs[k];
            controller.startRipple(
                explodeNode,
                dir,
                color,
                0.5f,
                1000 + random(600),
                BEHAVIOR_FEISTY);
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(FireworksAnimation)
