# Proposed New Animations

This document outlines new animation concepts for the Chromance firmware, derived from an analysis of the existing codebase and topology.

## 1. Meteor Shower (Digital Rain)

**Concept:**
Bright "raindrops" or "meteors" spawn at the top of the structure and trickle downwards to the bottom node, simulating rain or a digital waterfall.

**Mechanics:**
-   **Spawn Points:** Top nodes (Nodes 0, 1, 2).
-   **Target:** Bottom node (Node 24).
-   **Movement Logic:** Utilizes `BEHAVIOR_CHASE` in conjunction with the static `Ripple::runnerNode` target.

**Implementation Details:**
-   **Class Name:** `MeteorShowerAnimation`
-   **Logic:**
    -   In `run()` (or `update()` if continuously spawning):
        -   Set `Ripple::runnerNode = 24`.
        -   Randomly pick one of the top nodes (0, 1, 2).
        -   Spawn a ripple:
            -   **Color:** High brightness White, Cyan, or Blue.
            -   **Behavior:** `BEHAVIOR_CHASE`.
            -   **Speed:** Medium-fast.
            -   **Lifespan:** Sufficient to reach the bottom (e.g., 2000-3000ms).

**Code Snippet (Conceptual):**
```cpp
void MeteorShowerAnimation::run()
{
    Ripple::runnerNode = 24; // Target bottom
    int startNode = random(3); // 0, 1, or 2
    
    // Find a valid direction downwards to start (optional, or just pick any connected segment)
    // Actually, startRipple takes a 'direction' (path index). 
    // We should pick a path that actually exists.
    int direction = 0; 
    // ... logic to find valid direction from startNode ...
    
    controller.startRipple(
        startNode, 
        direction, 
        0xFFFFFF, // White
        0.7f, 
        3000, 
        BEHAVIOR_CHASE
    );
}
```

## 2. Searchlight (Radar Scanner)

**Concept:**
A rotating beam of light sweeps around the center of the structure, illuminating segments as it passes over them.

**Mechanics:**
-   **Math:** Uses `atan2(y, x)` to calculate the angle of each segment relative to the center of the display.
-   **Rendering:** Directly manipulates the `LedController` rather than using `Ripple` agents.

**Implementation Details:**
-   **Class Name:** `SearchlightAnimation`
-   **Center Point:** Node 15 (`nodePositions[15]` is approx {40, 13}, which is roughly center of 80x26 grid).
-   **Logic:**
    -   Maintain a `float currentAngle` state variable.
    -   In `update()`:
        -   Increment `currentAngle`.
        -   Clear all LEDs (fade out).
        -   Iterate through all segments `s`.
        -   Get position of `s` (average of its two connected nodes).
        -   Calculate `segmentAngle = atan2(dy, dx)`.
        -   If `abs(segmentAngle - currentAngle)` is small (within beam width), light up segment.
        -   Color can be `baseColor` or a specific "radar green".

## 3. Bio-Pulse (Breathing)

**Concept:**
The entire structure behaves like a living organism, pulsing with a rhythmic breath. This is a global effect rather than a traveling wave.

**Mechanics:**
-   **Waveform:** Sine wave based on `millis()`.
-   **Spatial Variation:** Phase shift based on distance from center (Node 15) to create an outward "breathing" motion.

**Implementation Details:**
-   **Class Name:** `BioPulseAnimation`
-   **Logic:**
    -   In `update()`:
        -   Calculate `time = millis()`.
        -   Iterate through all Nodes or Segments.
        -   For each entity:
            -   Calculate `dist` from center (Node 15).
            -   `brightness = sin(time * speed - dist * phase_factor)`.
            -   Map `brightness` (-1 to 1) to (MinBrightness to MaxBrightness).
            -   Set color.
    -   Uses direct `ledController.setPixel` or `setSegment` (if available, otherwise loop pixels).

## 4. Glitch / Spark

**Concept:**
Simulates a malfunctioning or highly energetic system with random, brief, intense flashes of light on random segments.

**Mechanics:**
-   **Randomness:** Stochastic triggering.
-   **Duration:** Very short (1-3 frames).

**Implementation Details:**
-   **Class Name:** `GlitchAnimation`
-   **Logic:**
    -   In `update()`:
        -   Small chance (e.g., 5%) to trigger a "spark".
        -   Pick random segment.
        -   Pick random color (usually White or erratic colors).
        -   Set all LEDs in segment to color.
        -   *Crucial:* These sparks need to clear themselves. Either use a `Ripple` with very short life (e.g., 100ms) and `BEHAVIOR_COUCH_POTATO` (stops immediately), or manage a list of active sparks.
        -   Using `controller.startRipple(..., BEHAVIOR_COUCH_POTATO)` is the easiest way to leverage existing cleanup logic.

```cpp
// Spark using Ripple system
controller.startRipple(
    random(Topology::numberOfNodes),
    random(Constants::MAX_PATHS_PER_NODE),
    0xFFFFFF,
    1.0f, // Fast
    100,  // Die quickly
    BEHAVIOR_COUCH_POTATO // Don't move
);
```
