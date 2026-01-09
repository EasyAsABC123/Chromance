#include "HeartbeatAnimation.h"
#include "../AnimationController.h"
#include "../Constants.h"

void HeartbeatAnimation::run()
{
  startTime = millis();
}

void HeartbeatAnimation::update()
{
  unsigned long time = millis() - startTime;
  unsigned long cycleTime = 1500; // 1.5s per heartbeat cycle
  unsigned long t = time % cycleTime;

  float brightness = 0.1f; // Base brightness (dim red)

  // First beat ("lub") - Sharp attack, fast decay
  if (t < 200)
  {
    float phase = t / 200.0f;
    // Triangle wave: 0 -> 1 -> 0
    // Peak at 50ms (0.25)
    if (phase < 0.25f)
      brightness += (phase / 0.25f) * 0.8f;
    else
      brightness += ((1.0f - phase) / 0.75f) * 0.8f;
  }
  // Second beat ("dub") - Slightly lower peak, slightly delayed
  else if (t >= 300 && t < 600)
  {
    float phase = (t - 300) / 300.0f;
    // Triangle wave
    // Peak at 100ms into the beat (0.33)
    if (phase < 0.33f)
      brightness += (phase / 0.33f) * 0.6f;
    else
      brightness += ((1.0f - phase) / 0.67f) * 0.6f;
  }

  // Clamp brightness
  if (brightness > 1.0f)
    brightness = 1.0f;

  // Calculate color (Red with calculated brightness)
  // HSV: Hue 0 (Red), Sat 255, Val scaled by brightness
  uint32_t color = controller.getLedController().ColorHSV(0, 255, (uint8_t)(100 * brightness));

  // Apply to all LEDs
  for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; segment++)
  {
    for (int led = 0; led < Constants::LEDS_PER_SEGMENT; led++)
    {
      // Extract RGB components from packed color
      byte r = (uint8_t)(color >> 16);
      byte g = (uint8_t)(color >> 8);
      byte b = (uint8_t)(color);

      controller.getLedController().setPixelColor(segment, led, r, g, b);
    }
  }
}
