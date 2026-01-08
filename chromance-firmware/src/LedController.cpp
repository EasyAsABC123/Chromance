#include "LedController.h"
#include "Utils.h"

LedController::LedController()
{
  for (int i = 0; i < Constants::NUMBER_OF_STRIPS; i++)
  {
    strips[i] = nullptr;
  }
}

LedController::~LedController()
{
  for (int i = 0; i < Constants::NUMBER_OF_STRIPS; i++)
  {
    if (strips[i] != nullptr)
    {
      delete strips[i];
      strips[i] = nullptr;
    }
  }
}

void LedController::initStrips()
{
  // check if already initialized to prevent double allocation
  if (strips[0] != nullptr)
    return;

#ifdef USING_DOTSTAR
  strips[Constants::BLUE_INDEX] = new Adafruit_DotStar(Constants::BLUE_LENGTH, Constants::BLUE_STRIP_DATA_PIN, Constants::BLUE_STRIP_CLOCK_PIN, DOTSTAR_BRG);
  strips[Constants::GREEN_INDEX] = new Adafruit_DotStar(Constants::GREEN_LENGTH, Constants::GREEN_STRIP_DATA_PIN, Constants::GREEN_STRIP_CLOCK_PIN, DOTSTAR_BRG);
  strips[Constants::RED_INDEX] = new Adafruit_DotStar(Constants::RED_LENGTH, Constants::RED_STRIP_DATA_PIN, Constants::RED_STRIP_CLOCK_PIN, DOTSTAR_BRG);
  strips[Constants::BLACK_INDEX] = new Adafruit_DotStar(Constants::BLACK_LENGTH, Constants::BLACK_STRIP_DATA_PIN, Constants::BLACK_STRIP_CLOCK_PIN, DOTSTAR_BRG);
#else
  strips[Constants::BLUE_INDEX] = new Adafruit_NeoPixel(Constants::BLUE_LENGTH, Constants::BLUE_STRIP_DATA_PIN, NEO_GRB + NEO_KHZ800);
  strips[Constants::GREEN_INDEX] = new Adafruit_NeoPixel(Constants::GREEN_LENGTH, Constants::GREEN_STRIP_DATA_PIN, NEO_GRB + NEO_KHZ800);
  strips[Constants::RED_INDEX] = new Adafruit_NeoPixel(Constants::RED_LENGTH, Constants::RED_STRIP_DATA_PIN, NEO_GRB + NEO_KHZ800);
  strips[Constants::BLACK_INDEX] = new Adafruit_NeoPixel(Constants::BLACK_LENGTH, Constants::BLACK_STRIP_DATA_PIN, NEO_GRB + NEO_KHZ800);
#endif
}

void LedController::begin()
{
  initStrips();
  clear();

  for (int i = 0; i < Constants::NUMBER_OF_STRIPS; i++)
  {
    strips[i]->begin();
    strips[i]->setBrightness(255);
    strips[i]->show();
  }
}

void LedController::clear()
{
  memset(ledColors, 0, sizeof(ledColors));
  for (int i = 0; i < Constants::NUMBER_OF_STRIPS; i++)
  {
    strips[i]->clear();
  }
}

void LedController::fade(float decay)
{
  for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; segment++)
  {
    for (int led = 0; led < Constants::LEDS_PER_SEGMENT; led++)
    {
      for (int k = 0; k < 3; k++)
      {
        ledColors[segment][led][k] = (byte)(ledColors[segment][led][k] * decay);
      }
    }
  }
}

void LedController::setPixelColor(int segment, int led, byte r, byte g, byte b)
{
  if (segment < 0 || segment >= Constants::NUMBER_OF_SEGMENTS || led < 0 || led >= Constants::LEDS_PER_SEGMENT)
    return;
  ledColors[segment][led][0] = r;
  ledColors[segment][led][1] = g;
  ledColors[segment][led][2] = b;
}

void LedController::addPixelColor(int segment, int led, byte r, byte g, byte b)
{
  if (segment < 0 || segment >= Constants::NUMBER_OF_SEGMENTS || led < 0 || led >= Constants::LEDS_PER_SEGMENT)
    return;

  int newR = ledColors[segment][led][0] + r;
  int newG = ledColors[segment][led][1] + g;
  int newB = ledColors[segment][led][2] + b;

  ledColors[segment][led][0] = (newR > 255) ? 255 : newR;
  ledColors[segment][led][1] = (newG > 255) ? 255 : newG;
  ledColors[segment][led][2] = (newB > 255) ? 255 : newB;
}

void LedController::show()
{
  for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; segment++)
  {
    for (int fromBottom = 0; fromBottom < Constants::LEDS_PER_SEGMENT; fromBottom++)
    {
      int stripIdx = Topology::ledAssignments[segment][0];
      int floorIndex = Topology::ledAssignments[segment][2];
      int ceilingIndex = Topology::ledAssignments[segment][1];

      int ledIndex = round(fmap(
          fromBottom,
          0, (Constants::LEDS_PER_SEGMENT - 1),
          floorIndex, ceilingIndex));

      strips[stripIdx]->setPixelColor(
          ledIndex,
          ledColors[segment][fromBottom][0],
          ledColors[segment][fromBottom][1],
          ledColors[segment][fromBottom][2]);
    }
  }

  for (int i = 0; i < Constants::NUMBER_OF_STRIPS; i++)
  {
    strips[i]->show();
  }
}

void LedController::rainbow()
{
  for (int i = 0; i < Constants::NUMBER_OF_STRIPS; i++)
  {
    strips[i]->rainbow();
    strips[i]->show();
  }
}

uint32_t LedController::ColorHSV(uint16_t hue, uint8_t sat, uint8_t val)
{
#ifdef USING_DOTSTAR
  return Adafruit_DotStar::ColorHSV(hue, sat, val);
#else
  return Adafruit_NeoPixel::ColorHSV(hue, sat, val);
#endif
}
