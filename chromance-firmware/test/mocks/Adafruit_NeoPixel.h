#ifndef ADAFRUIT_NEOPIXEL_MOCK_H
#define ADAFRUIT_NEOPIXEL_MOCK_H

#include <vector>
#include <cstdint>
#include <algorithm>
#include "Arduino.h"

// Constants
#define NEO_GRB 0
#define NEO_KHZ800 0

class Adafruit_NeoPixel
{
public:
  Adafruit_NeoPixel(uint16_t n, uint16_t p, uint8_t t) : numLEDs(n), pin(p), type(t)
  {
    pixels.resize(n, 0);
  }

  void begin() {}
  void show()
  {
    // Maybe notify a listener?
  }
  void clear()
  {
    std::fill(pixels.begin(), pixels.end(), 0);
  }
  void setBrightness(uint8_t) {}

  void setPixelColor(uint16_t n, uint8_t r, uint8_t g, uint8_t b)
  {
    if (n < pixels.size())
    {
      pixels[n] = ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
    }
  }

  void setPixelColor(uint16_t n, uint32_t c)
  {
    if (n < pixels.size())
    {
      pixels[n] = c;
    }
  }

  uint32_t getPixelColor(uint16_t n) const
  {
    if (n < pixels.size())
      return pixels[n];
    return 0;
  }

  uint16_t numPixels() const { return numLEDs; }

  static uint32_t Color(uint8_t r, uint8_t g, uint8_t b)
  {
    return ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
  }

  static uint32_t ColorHSV(uint16_t hue, uint8_t sat, uint8_t val)
  {
    uint8_t r, g, b;

    // Remap hue from 0-65535 to 0-1529
    uint32_t hue32 = (uint32_t)hue * 1530;
    hue32 = (hue32 + 32768) / 65536;
    uint16_t h = hue32;

    if (h < 255)
    {
      r = 255;
      g = h;
      b = 0;
    }
    else if (h < 510)
    {
      r = 510 - h;
      g = 255;
      b = 0;
    }
    else if (h < 765)
    {
      r = 0;
      g = 255;
      b = h - 510;
    }
    else if (h < 1020)
    {
      r = 0;
      g = 1020 - h;
      b = 255;
    }
    else if (h < 1275)
    {
      r = h - 1020;
      g = 0;
      b = 255;
    }
    else
    {
      r = 255;
      g = 0;
      b = 1530 - h;
    }

    // Apply saturation and value
    uint32_t v1 = 1 + val;
    uint16_t s1 = 1 + sat;
    uint8_t s2 = 255 - sat;

    r = (uint8_t)(((((r * s1) >> 8) + s2) * v1) >> 8);
    g = (uint8_t)(((((g * s1) >> 8) + s2) * v1) >> 8);
    b = (uint8_t)(((((b * s1) >> 8) + s2) * v1) >> 8);

    return ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
  }

  void rainbow(uint16_t first_hue = 0, int8_t reps = 1, uint8_t saturation = 255, uint8_t brightness = 255, bool gammify = true)
  {
    for (uint16_t i = 0; i < numLEDs; i++)
    {
      uint16_t hue = first_hue + (i * reps * 65536) / numLEDs;
      uint32_t color = ColorHSV(hue, saturation, brightness);
      setPixelColor(i, color);
    }
  }

  // Public for inspection
  std::vector<uint32_t> pixels;

private:
  uint16_t numLEDs;
  uint16_t pin;
  uint8_t type;
};

#endif // ADAFRUIT_NEOPIXEL_MOCK_H
