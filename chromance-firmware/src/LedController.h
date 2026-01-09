#ifndef LEDCONTROLLER_H
#define LEDCONTROLLER_H

#include <Arduino.h>
#include "Constants.h"
#include "Topology.h"

// Define macros for library inclusion based on Constants or compile definitions
#ifdef USING_DOTSTAR
#include <Adafruit_DotStar.h>
#elif defined(USING_NEOPIXEL) || !defined(USING_DOTSTAR) // Default to NeoPixel
#include <Adafruit_NeoPixel.h>
#ifndef USING_NEOPIXEL
#define USING_NEOPIXEL
#endif
#endif

class LedController
{
public:
  LedController();
  ~LedController(); // Clean up if we use new
  void begin();
  void show();
  void clear();
  void fade(float decay);

  // Accessors for ripple logic
  void setPixelColor(int segment, int led, byte r, byte g, byte b);
  void addPixelColor(int segment, int led, byte r, byte g, byte b);

  uint32_t ColorHSV(uint16_t hue, uint8_t sat, uint8_t val);

  // Raw access if needed (prefer methods above)
  // [Segment][LED][RGB]
  byte ledColors[Constants::NUMBER_OF_SEGMENTS][Constants::LEDS_PER_SEGMENT][3];

  void rainbow(uint16_t first_hue = 0);

#ifdef USING_DOTSTAR
  Adafruit_DotStar *getStrip(int index) { return strips[index]; }
#else
  Adafruit_NeoPixel *getStrip(int index) { return strips[index]; }
#endif

private:
#ifdef USING_DOTSTAR
  Adafruit_DotStar *strips[Constants::NUMBER_OF_STRIPS];
#else
  Adafruit_NeoPixel *strips[Constants::NUMBER_OF_STRIPS];
#endif

  void initStrips();
};

#endif // LEDCONTROLLER_H
