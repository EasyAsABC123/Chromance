# Proposed & Implemented Animations

This document outlines new animation concepts for the Chromance firmware.

## 1. Meteor Shower (Implemented)
**Concept:** Bright "raindrops" trickling downwards.
**Mechanics:** Spawns at top nodes, chases to bottom using `BEHAVIOR_CHASE`.

## 2. Searchlight (Implemented)
**Concept:** Rotating radar beam.
**Mechanics:** Uses `atan2` to calculate angle of segments relative to center.

## 3. Bio-Pulse (Implemented)
**Concept:** Rhythmic breathing effect.
**Mechanics:** Sine wave brightness based on distance from center.

## 4. Glitch (Implemented)
**Concept:** Random electrical sparks.
**Mechanics:** Short-lived, high-speed ripples or direct segment flashes.

## 5. Water Pour (Implemented)
**Concept:** Water trickling down and filling up from the bottom.
**Mechanics:**
-   **Physics:** Drops fall, split at junctions, and accumulate in `segmentLevels`.
-   **Visuals:** Blue water filling up, Cyan drops falling. Slosh effect on surface.

## 6. Inferno (Fire)
**Concept:**
Simulates a roaring fire starting from the bottom of the structure and rising upwards. Based on the classic "Fire2012" algorithm but adapted for the node/segment topology.

**Mechanics:**
-   **Heat Generation:** Bottom segments (connected to bottom nodes) randomly generate "heat".
-   **Convection:** Heat moves from lower segments to upper connected segments.
-   **Cooling:** All segments cool down over time.
-   **Mapping:** Heat values (0-255) map to a Color Palette (Black -> Red -> Orange -> White).

**Implementation Details:**
-   **Class Name:** `InfernoAnimation`
-   **State:** float array `heat[Constants::NUMBER_OF_SEGMENTS]`.
-   **Logic:**
    -   Identify "Bottom" segments (connected to floor nodes).
    -   In `update()`:
        -   **Cooling:** `heat[s] = max(0.0f, heat[s] - randomCooling)`.
        -   **Drift:** For each segment `s`, transfer some heat to segments *above* it (using `Topology` to find upward neighbors).
        -   **Ignition:** Randomly add bursts of heat to bottom segments.
        -   **Render:** Convert `heat[s]` to RGB using a fire palette and apply to all LEDs in segment (perhaps with some noise/variation per LED).

## 7. Bouncing Balls
**Concept:**
Simulates multiple glowing balls falling under gravity and bouncing off the ground (bottom nodes).

**Mechanics:**
-   **Physics:** Gravity accelerates balls down. Impact with bottom nodes reverses velocity with a coefficient of restitution (energy loss).
-   **Visuals:** Balls leave a short trail. Color changes on bounce or per ball.

**Implementation Details:**
-   **Class Name:** `BouncingBallsAnimation`
-   **Struct:** `Ball { int segment; float position; float velocity; uint32_t color; }`
-   **Logic:**
    -   Similar pathfinding to `WaterAnimation` (falling down).
    -   When `position >= 1.0` and node is "Bottom" (no lower neighbors):
        -   `velocity = -velocity * restitution` (bounce).
        -   If velocity is small, ball dies or re-spawns at top.
    -   When `position <= 0.0` (moving up after bounce):
        -   Move to upper segment if possible.
        -   If `velocity` reaches 0, gravity pulls it back down.
    -   Manage `std::vector<Ball>`.

## 8. Fireflies (Twinkle)
**Concept:**
A calm, magical effect where random LEDs gently fade in and out like fireflies in a forest.

**Mechanics:**
-   **Particles:** Invisible agents placed on random LEDs.
-   **Lifecycle:** State machine: Hidden -> Fading In -> Lit -> Fading Out -> Hidden.
-   **Colors:** Golden yellow, green, or random.

**Implementation Details:**
-   **Class Name:** `FirefliesAnimation`
-   **Struct:** `Firefly { int segment; int led; float brightness; int state; float speed; }`
-   **Logic:**
    -   Maintain fixed number of fireflies (e.g., 20).
    -   In `update()`:
        -   If state is Hidden: small chance to start Fading In at new random location.
        -   Update brightness based on state.
        -   Draw pixel using cubic easing for smooth pulse.

## 9. Fireworks
**Concept:**
Rockets launch from the ground, travel up to a random height/node, and explode into a burst of particles.

**Mechanics:**
-   **Phase 1 (Launch):** A single bright ripple travels from bottom to a target node.
-   **Phase 2 (Explosion):** Upon reaching target, spawn multiple ripples moving outward in all connected directions.
-   **Phase 3 (Decay):** Explosion ripples have short life and fade out.

**Implementation Details:**
-   **Class Name:** `FireworksAnimation`
-   **Logic:**
    -   Utilize `AnimationController::startRipple`.
    -   **Launch:** Start ripple at bottom node, targeting a random upper node (`BEHAVIOR_CHASE` or pathfinding).
    -   **Trigger:** When launch ripple dies (or reaches destination), trigger explosion.
    -   **Explosion:** Iterate all paths from target node. Start `Ripple` on each path:
        -   `BEHAVIOR_ALWAYS_LEFT` / `RIGHT` or `EXPLODING`.
        -   Color: Random saturated color.
        -   Speed: Fast, decaying.
