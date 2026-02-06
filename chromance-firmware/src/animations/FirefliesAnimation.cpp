#include "FirefliesAnimation.h"
#include "../AnimationController.h"
#include "../Constants.h"

FirefliesAnimation::FirefliesAnimation(AnimationController &controller) : Animation(controller) {}

void FirefliesAnimation::run()
{
    for(int i=0; i<NUM_FIREFLIES; i++) {
        flies[i].state = 0; // Hidden
        flies[i].brightness = 0.0f;
    }
}

void FirefliesAnimation::update()
{
    LedController& lc = controller.getLedController();
    
    for(int i=0; i<NUM_FIREFLIES; i++) {
        Firefly& f = flies[i];
        
        switch(f.state) {
            case 0: // Hidden
                if (random(100) < 2) { // 2% chance to spawn
                    f.segment = random(Constants::NUMBER_OF_SEGMENTS);
                    f.led = random(Constants::LEDS_PER_SEGMENT);
                    f.state = 1; // Fade In
                    f.brightness = 0.0f;
                    f.speed = 0.02f + (random(100) / 5000.0f); // 0.02 - 0.04
                    
                    // Color: Yellow/Greenish or custom
                    if (random(2)) {
                        f.color = 0xFFFF00; // Yellow
                    } else {
                        f.color = 0xADFF2F; // GreenYellow
                    }
                }
                break;
                
            case 1: // Fading In
                f.brightness += f.speed;
                if (f.brightness >= 1.0f) {
                    f.brightness = 1.0f;
                    f.state = 2; // Lit
                }
                break;
                
            case 2: // Lit
                // Hold for a bit? Or immediately fade out?
                // Let's hold based on random chance
                if (random(100) < 5) {
                    f.state = 3; // Start fading out
                }
                break;
                
            case 3: // Fading Out
                f.brightness -= f.speed;
                if (f.brightness <= 0.0f) {
                    f.brightness = 0.0f;
                    f.state = 0; // Hidden
                }
                break;
        }
        
        if (f.state != 0 && f.brightness > 0.001f) {
            byte r = (f.color >> 16) & 0xFF;
            byte g = (f.color >> 8) & 0xFF;
            byte b = f.color & 0xFF;
            
            // Apply easing? Smoothstep: x*x*(3-2*x)
            float val = f.brightness * f.brightness * (3.0f - 2.0f * f.brightness);
            
            lc.addPixelColor(f.segment, f.led, 
                (byte)(r * val), 
                (byte)(g * val), 
                (byte)(b * val)
            );
        }
    }
}

#include "../AnimationRegistry.h"
REGISTER_ANIMATION(FirefliesAnimation)
