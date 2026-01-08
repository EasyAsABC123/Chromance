#include "ripple.h"
#include "Utils.h"

// #define DEBUG_ADVANCEMENT
// #define DEBUG_RENDERING
// #define DEBUG_AGE

Ripple::Ripple(int id) : rippleId(id)
{
    // Serial.print("Instanced ripple #");
    // Serial.println(rippleId);
}

void Ripple::start(int node, int direction, unsigned long color, float speed, unsigned long lifespan, RippleBehavior behavior)
{
    Ripple::color = color;
    Ripple::speed = speed;
    Ripple::lifespan = (lifespan == 0) ? 1 : lifespan;
    Ripple::behavior = behavior;

    birthday = millis();
    pressure = 0;
    state = STATE_WITHIN_NODE;

    Ripple::node = node;
    Ripple::direction = direction;

    justStarted = true;

    Serial.print("Ripple ");
    Serial.print(rippleId);
    Serial.print(" starting at node ");
    Serial.print(node);
    Serial.print(" direction ");
    Serial.println(direction);
}

void Ripple::renderLed(LedController &ledController, unsigned long age)
{
    // In Ripple logic: 'node' maps to segment index, 'direction' maps to LED index within segment
    int segment = node;
    int led = direction;

    // Check bounds just in case
    if (segment < 0 || segment >= Constants::NUMBER_OF_SEGMENTS || led < 0 || led >= Constants::LEDS_PER_SEGMENT)
    {
        return;
    }

    byte val0 = (byte)fmap(float(age), 0.0f, float(lifespan), (float)((color >> 8) & 0xFF), 0.0f);
    byte val1 = (byte)fmap(float(age), 0.0f, float(lifespan), (float)((color >> 16) & 0xFF), 0.0f);
    byte val2 = (byte)fmap(float(age), 0.0f, float(lifespan), (float)(color & 0xFF), 0.0f);

    ledController.addPixelColor(segment, led, val0, val1, val2);
}

void Ripple::advance(LedController &ledController)
{
    unsigned long age = millis() - birthday;

    if (state == STATE_DEAD)
    {
        return;
    }

    pressure += fmap(float(age), 0.0, float(lifespan), speed, 0.0); // Ripple slows down as it ages
    // TODO: Motion of ripple is severely affected by loop speed. Make it time invariant

    if (pressure < 1 && (state == STATE_TRAVEL_UP || state == STATE_TRAVEL_DOWN))
    {
        // Ripple is visible but hasn't moved - render it to avoid flickering
        renderLed(ledController, age);
    }

    while (pressure >= 1)
    {
#ifdef DEBUG_ADVANCEMENT
        Serial.print("---- Ripple ");
        Serial.print(rippleId);
        Serial.println(" advancing:");
#endif

        switch (state)
        {
        case STATE_WITHIN_NODE:
        {
            if (justStarted)
            {
                justStarted = false;
            }
            else
            {
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Picking direction out of node ");
                Serial.print(node);
                Serial.print(" with agr. ");
                Serial.println(behavior);
#endif

                int newDirection = -1;

                int sharpLeft = (direction + 1) % Constants::MAX_PATHS_PER_NODE;
                int wideLeft = (direction + 2) % Constants::MAX_PATHS_PER_NODE;
                int forward = (direction + 3) % Constants::MAX_PATHS_PER_NODE;
                int wideRight = (direction + 4) % Constants::MAX_PATHS_PER_NODE;
                int sharpRight = (direction + 5) % Constants::MAX_PATHS_PER_NODE;

                if (behavior <= BEHAVIOR_ANGRY)
                { // Semi-random aggressive turn mode
                    // The more aggressive a ripple, the tighter turns it wants to make.
                    // If there aren't any segments it can turn to, we need to adjust its behavior.
                    int anger = (int)behavior;
                    int forwardConnection = Topology::nodeConnections[node][forward];

                    int attempts = 0;
                    while (newDirection < 0 && attempts < 10)
                    {
                        attempts++;
                        if (anger == BEHAVIOR_COUCH_POTATO)
                        {

                            // We can't go straight ahead - we need to take a rest
#ifdef DEBUG_ADVANCEMENT
                            Serial.println("  Never continue ... too lazy - stopping");
#endif
                            // Die now
                            age = lifespan;
                            break;
                        }

                        if (anger == BEHAVIOR_LAZY)
                        {

                            if (forwardConnection < 0)
                            {
                                // We can't go straight ahead - we need to take a rest
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can't go straight - stopping");
#endif
                                // Die now
                                age = lifespan;
                                break;
                                // break;
                            }
                            else
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Going forward");
#endif
                                newDirection = forward;
                            }
                        }

                        if (anger == BEHAVIOR_WEAK)
                        {

                            if (forwardConnection < 0)
                            {
                                // We can't go straight ahead - we need to take a more aggressive angle
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can't go straight - picking more agr. path");
#endif
                                anger++;
                            }
                            else
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Going forward");
#endif
                                newDirection = forward;
                            }
                        }

                        if (anger == BEHAVIOR_FEISTY)
                        {
                            int leftConnection = Topology::nodeConnections[node][wideLeft];
                            int rightConnection = Topology::nodeConnections[node][wideRight];

                            if (leftConnection >= 0 && rightConnection >= 0)
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Turning left or right at random");
#endif
                                newDirection = random(2) ? wideLeft : wideRight;
                            }
                            else if (leftConnection >= 0)
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can only turn left");
#endif
                                newDirection = wideLeft;
                            }
                            else if (rightConnection >= 0)
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can only turn right");
#endif
                                newDirection = wideRight;
                            }
                            else
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can't make wide turn - picking more agr. path");
#endif
                                anger += 1; // Can't take shallow turn - must become more aggressive
                            }
                        }

                        if (anger == BEHAVIOR_ANGRY)
                        {
                            int leftConnection = Topology::nodeConnections[node][sharpLeft];
                            int rightConnection = Topology::nodeConnections[node][sharpRight];

                            if (leftConnection >= 0 && rightConnection >= 0)
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Turning left or right at random");
#endif
                                newDirection = random(2) ? sharpLeft : sharpRight;
                            }
                            else if (leftConnection >= 0)
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can only turn left");
#endif
                                newDirection = sharpLeft;
                            }
                            else if (rightConnection >= 0)
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can only turn right");
#endif
                                newDirection = sharpRight;
                            }
                            else
                            {
#ifdef DEBUG_ADVANCEMENT
                                Serial.println("  Can't make tight turn - picking less agr. path");
#endif
                                anger--; // Can't take tight turn - must become less aggressive
                            }
                        }

                        // Note that this can't handle some circumstances,
                        // like a node with segments in nothing but the 0 and 3 positions.
                        // Good thing we don't have any of those!

                    } // End while loop

                    if (newDirection < 0)
                    {
                        // If we couldn't find a direction after attempts, kill the ripple to prevent hanging
                        state = STATE_DEAD;
                        return;
                    }
                }
                else if (behavior == BEHAVIOR_ALWAYS_RIGHT)
                {
                    for (int i = 1; i < Constants::MAX_PATHS_PER_NODE; i++)
                    {
                        int possibleDirection = (direction + i) % Constants::MAX_PATHS_PER_NODE;

                        if (Topology::nodeConnections[node][possibleDirection] >= 0)
                        {
                            newDirection = possibleDirection;
                            break;
                        }
                    }
#ifdef DEBUG_ADVANCEMENT
                    Serial.println("  Turning as rightward as possible");
#endif
                }
                else if (behavior == BEHAVIOR_ALWAYS_LEFT)
                {
                    for (int i = 5; i >= 1; i--)
                    {
                        int possibleDirection = (direction + i) % Constants::MAX_PATHS_PER_NODE;

                        if (Topology::nodeConnections[node][possibleDirection] >= 0)
                        {
                            newDirection = possibleDirection;
                            break;
                        }
                    }
#ifdef DEBUG_ADVANCEMENT
                    Serial.println("  Turning as leftward as possible");
#endif
                }
                else if (behavior == BEHAVIOR_EXPLODING)
                {
                    for (int i = 5; i >= 1; i--)
                    {
                        int possibleDirection = (direction + i) % Constants::MAX_PATHS_PER_NODE;

                        if (Topology::nodeConnections[node][possibleDirection] >= 0 && (possibleDirection != node))
                        {
                            newDirection = possibleDirection;
                            // start
                        }
                    }

#ifdef DEBUG_ADVANCEMENT
                    Serial.println(" Exploding !");
#endif
                }

#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Leaving node ");
                Serial.print(node);
                Serial.print(" in direction ");
                Serial.println(newDirection);
#endif
                if (newDirection >= 0)
                {
                    direction = newDirection;
                }
            } // End else from 'if (justStarted) {'

            node = Topology::nodeConnections[node][direction]; // Look up which segment we're on
            if (node < 0 || node >= Constants::NUMBER_OF_SEGMENTS)
            {
                Serial.print("Uhoh, node out of bound at line 296 :");
                Serial.println(node);
                state = STATE_DEAD;
                return;
            }
#ifdef DEBUG_ADVANCEMENT
            Serial.print("  and entering segment ");
            Serial.println(node);
#endif

            if (direction == 5 || direction == 0 || direction == 1)
            { // Top half of the node
#ifdef DEBUG_ADVANCEMENT
                Serial.println("  (starting at bottom)");
#endif
                state = STATE_TRAVEL_UP;
                direction = 0; // Starting at bottom of segment
            }
            else
            {
#ifdef DEBUG_ADVANCEMENT
                Serial.println("  (starting at top)");
#endif
                state = STATE_TRAVEL_DOWN;
                direction = Constants::LEDS_PER_SEGMENT - 1; // Starting at top of LED-strip
            }
            break;
        }

        case STATE_TRAVEL_UP:
        {
            direction++;

            if (direction >= Constants::LEDS_PER_SEGMENT)
            {
                // We've reached the top!
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Reached top of seg. ");
                Serial.println(node);
#endif
                // Enter the new node.
                int segment = node;

                if (node < 0 || node >= Constants::NUMBER_OF_SEGMENTS)
                {
                    state = STATE_DEAD;
                    return;
                }

                node = Topology::segmentConnections[node][0];
                if (node < 0 || node >= Constants::NUMBER_OF_NODES)
                {
                    state = STATE_DEAD;
                    return;
                }
                bool foundConnection = false;
                for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
                {
                    // Figure out from which direction the ripple is entering the node.
                    // Allows us to exit in an appropriately aggressive direction.
                    int incomingConnection = Topology::nodeConnections[node][i];
                    if (incomingConnection == segment)
                    {
                        direction = i;
                        foundConnection = true;
                        break;
                    }
                }
                if (!foundConnection)
                {
                    // Serial.println("Topology mismatch: entered node but no back-connection found");
                    state = STATE_DEAD;
                    return;
                }
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Entering node ");
                Serial.print(node);
                Serial.print(" from direction ");
                Serial.println(direction);
#endif
                state = STATE_WITHIN_NODE;
            }
            else
            {
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Moved up to seg. ");
                Serial.print(node);
                Serial.print(" LED ");
                Serial.println(direction);
#endif
            }
            break;
        }

        case STATE_TRAVEL_DOWN:
        {
            direction--;
            if (direction < 0)
            {
                // We've reached the bottom!
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Reached bottom of seg. ");
                Serial.println(node);
#endif
                // Enter the new node.
                int segment = node;

                if (node < 0 || node >= Constants::NUMBER_OF_SEGMENTS)
                {
                    state = STATE_DEAD;
                    return;
                }

                node = Topology::segmentConnections[node][1];

                if (node < 0 || node >= Constants::NUMBER_OF_NODES)
                {
                    state = STATE_DEAD;
                    return;
                }

                bool foundConnection = false;
                for (int i = 0; i < Constants::MAX_PATHS_PER_NODE; i++)
                {
                    // Figure out from which direction the ripple is entering the node.
                    // Allows us to exit in an appropriately aggressive direction.
                    int incomingConnection = Topology::nodeConnections[node][i];
                    if (incomingConnection == segment)
                    {
                        direction = i;
                        foundConnection = true;
                        break;
                    }
                }
                if (!foundConnection)
                {
                    // Serial.println("Topology mismatch: entered node but no back-connection found");
                    state = STATE_DEAD;
                    return;
                }
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Entering node ");
                Serial.print(node);
                Serial.print(" from direction ");
                Serial.println(direction);
#endif
                state = STATE_WITHIN_NODE;
            }
            else
            {
#ifdef DEBUG_ADVANCEMENT
                Serial.print("  Moved down to seg. ");
                Serial.print(node);
                Serial.print(" LED ");
                Serial.println(direction);
#endif
            }
            break;
        }

        default:
            break;
        }

        pressure -= 1;

        if (state == STATE_TRAVEL_UP || state == STATE_TRAVEL_DOWN)
        {
            // Ripple is visible - render it
            renderLed(ledController, age);
        }
    }

#ifdef DEBUG_AGE
    Serial.print("  Age is now ");
    Serial.print(age);
    Serial.print('/');
    Serial.println(lifespan);
#endif

    if (lifespan && age >= lifespan)
    {
        // We STATE_DEAD
#ifdef DEBUG_AGE
        Serial.println("  Lifespan is up! Ripple is STATE_DEAD.");
#endif
        state = STATE_DEAD;
        node = direction = pressure = age = 0;
    }

#ifdef DEBUG_RENDERING
    Serial.print("Rendering ripple position (");
    Serial.print(node);
    Serial.print(',');
    Serial.print(direction);
    Serial.print(") at Strip ");
    Serial.print(strip);
    Serial.print(", LED ");
    Serial.print(led);
    Serial.print(", color 0x");
    for (int i = 0; i < 3; i++)
    {
        if (ledColors[node][direction][i] <= 0x0F)
        {
            Serial.print('0');
        }
        Serial.print(ledColors[node][direction][i], HEX);
    }
    Serial.println();
#endif
}