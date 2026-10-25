#include "ChristmasAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"
#include "../Constants.h"
#include "../AnimationRegistry.h"

void ChristmasAnimation::run() {
  LedController &lc = controller.getLedController();
  lc.clear();

  const uint32_t now = millis();
  nextTempoChange = now + (uint32_t)random(8000, 15000);
  tempoFast = false;

  for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; ++segment) {
    for (int led = 0; led < Constants::LEDS_PER_SEGMENT; ++led) {
      colorIndex[segment][led] = (uint8_t)random(4);

      // Arranque desigual: la mayoría tenue, algunas medias y unas pocas brillantes.
      brightness[segment][led] = (uint8_t)random(0, 55);
      targetBrightness[segment][led] = chooseBrightness();
      nextChange[segment][led] = now + (uint32_t)random(180, 1800);
      sparkleUntil[segment][led] = 0;
      sparkleActive[segment][led] = false;
    }
  }
}

uint8_t ChristmasAnimation::chooseBrightness() {
  const long roll = random(100);
  if (roll < 35) return (uint8_t)random(0, 18);     // casi apagada
  if (roll < 65) return (uint8_t)random(18, 65);    // tenue
  if (roll < 88) return (uint8_t)random(65, 145);   // media
  return (uint8_t)random(145, 225);                 // brillante, menos frecuente
}

void ChristmasAnimation::update() {
  LedController &lc = controller.getLedController();
  const uint32_t now = millis();

  // El ritmo general cambia cada cierto tiempo, sin sincronizar las luces entre sí.
  if ((int32_t)(now - nextTempoChange) >= 0) {
    tempoFast = !tempoFast;
    nextTempoChange = now + (uint32_t)random(8000, 16000);
  }

  for (int segment = 0; segment < Constants::NUMBER_OF_SEGMENTS; ++segment) {
    for (int led = 0; led < Constants::LEDS_PER_SEGMENT; ++led) {
      uint8_t &current = brightness[segment][led];
      uint8_t &target = targetBrightness[segment][led];

      if (sparkleActive[segment][led] &&
          (int32_t)(now - sparkleUntil[segment][led]) >= 0) {
        sparkleActive[segment][led] = false;
        target = chooseBrightness();
      }

      if ((int32_t)(now - nextChange[segment][led]) >= 0) {
        target = chooseBrightness();

        // Pequeños destellos blancos/dorados, poco frecuentes y breves.
        if (!sparkleActive[segment][led] && random(1000) < 9) {
          sparkleActive[segment][led] = true;
          sparkleUntil[segment][led] = now + (uint32_t)random(120, 320);
          target = (uint8_t)random(235, 256);
        } else if (random(100) < 12) {
          // El color cambia de vez en cuando, no en cada parpadeo.
          colorIndex[segment][led] = (uint8_t)random(4);
        }

        const uint32_t interval = tempoFast
          ? (uint32_t)random(180, 650)
          : (uint32_t)random(500, 1900);
        nextChange[segment][led] = now + interval;
      }

      // Respuesta algo más rápida hacia el brillo objetivo; cada LED va a su ritmo.
      const uint8_t step = tempoFast ? 11 : 6;
      if (current < target) {
        const uint8_t delta = (uint8_t)(target - current);
        current += (delta > step) ? step : delta;
      } else if (current > target) {
        const uint8_t delta = (uint8_t)(current - target);
        current -= (delta > step) ? step : delta;
      }

      uint8_t r = 0, g = 0, b = 0;

      if (sparkleActive[segment][led]) {
        // Destello blanco cálido, resaltado frente a los colores de base.
        r = 255; g = 218; b = 150;
      } else {
        switch (colorIndex[segment][led]) {
          case 0:  // Rojo
            r = 255; g = 8; b = 4;
            break;
          case 1:  // Verde
            r = 5; g = 255; b = 18;
            break;
          case 2:  // Dorado
            r = 255; g = 105; b = 8;
            break;
          default: // Blanco cálido
            r = 255; g = 190; b = 105;
            break;
        }
      }

      r = (uint16_t)r * current / 255;
      g = (uint16_t)g * current / 255;
      b = (uint16_t)b * current / 255;

      lc.setPixelColor(segment, led, r, g, b);
    }
  }
}

REGISTER_ANIMATION(ChristmasAnimation)
