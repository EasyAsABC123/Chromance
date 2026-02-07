#ifndef LIGHTNINGANIMATION_H
#define LIGHTNINGANIMATION_H

#include "Animation.h"

class LightningAnimation : public Animation
{
public:
    LightningAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    const char *getName() const override { return "Lightning"; }

private:
    float flashIntensity[40]; // One per segment
    unsigned long nextStrikeTime;
};

#endif
