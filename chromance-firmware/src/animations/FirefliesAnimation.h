#ifndef FIREFLIESANIMATION_H
#define FIREFLIESANIMATION_H

#include "Animation.h"

struct Firefly {
    int segment;
    int led;
    float brightness; // 0.0 to 1.0
    int state; // 0: Hidden, 1: Fading In, 2: Lit, 3: Fading Out
    float speed;
    uint32_t color;
};

class FirefliesAnimation : public Animation
{
public:
    FirefliesAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    const char *getName() const override { return "Fireflies"; }

private:
    static const int NUM_FIREFLIES = 20;
    Firefly flies[NUM_FIREFLIES];
};

#endif
