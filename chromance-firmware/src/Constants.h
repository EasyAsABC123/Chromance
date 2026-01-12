#ifndef CONSTANTS_H
#define CONSTANTS_H

#include <Arduino.h>

namespace Constants
{

// LED Type Configuration
// Uncomment the one you want to use
#ifndef USING_NEOPIXEL
// #define USING_NEOPIXEL
#endif
  // #define USING_DOTSTAR

  constexpr const char *HOSTNAME = "Chromance";

  constexpr int NUMBER_OF_ANIMATIONS = 7;
  constexpr int NUMBER_OF_RIPPLES = 30;
  constexpr int RIPPLE_TIMEOUT = NUMBER_OF_RIPPLES * 1000;
  constexpr int ANIMATION_TIME = 3000;

  constexpr int NUMBER_OF_NODES = 25;
  constexpr int MAX_PATHS_PER_NODE = 6;

  constexpr int NUMBER_OF_SEGMENTS = 40;
  constexpr int SIDES_PER_SEGMENT = 2;
  constexpr int LEDS_PER_SEGMENT = 14;
  constexpr int NUM_OF_PIXELS = NUMBER_OF_SEGMENTS * LEDS_PER_SEGMENT;

  constexpr int NUMBER_OF_STRIPS = 4;

  constexpr int BLUE_LENGTH = 154;
  constexpr int GREEN_LENGTH = 168;
  constexpr int RED_LENGTH = 84;
  constexpr int BLACK_LENGTH = 154;

  constexpr int BLUE_INDEX = 0;
  constexpr int GREEN_INDEX = 1;
  constexpr int RED_INDEX = 2;
  constexpr int BLACK_INDEX = 3;

  // Pin Configuration
  constexpr int BLUE_STRIP_DATA_PIN = 33;
  constexpr int GREEN_STRIP_DATA_PIN = 32;
  constexpr int RED_STRIP_DATA_PIN = 2;
  constexpr int BLACK_STRIP_DATA_PIN = 4;

  // DotStar specific pins
  constexpr int BLUE_STRIP_CLOCK_PIN = 2;
  constexpr int GREEN_STRIP_CLOCK_PIN = 4;
  constexpr int RED_STRIP_CLOCK_PIN = 17;
  constexpr int BLACK_STRIP_CLOCK_PIN = 18;

  // Pulse Configuration
  constexpr bool randomPulsesEnabled = true;
  constexpr bool cubePulsesEnabled = true;
  constexpr bool starburstPulsesEnabled = true;
  constexpr bool centerPulseEnabled = true;
  constexpr bool rainbowEnabled = true;
  constexpr bool chaseEnabled = true;
  constexpr bool heartbeatEnabled = true;
  constexpr int RAINBOW_BRIGHTNESS = 50;
  constexpr int MAX_CURRENT_MA = 2500; // Limit total current to 2500mA to prevent voltage drop

  constexpr int randomPulseTime = 2000; // ms

} // namespace Constants

#endif // CONSTANTS_H
