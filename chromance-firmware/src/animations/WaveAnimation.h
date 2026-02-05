#ifndef WAVEANIMATION_H
#define WAVEANIMATION_H

#include "Animation.h"

class WaveAnimation : public Animation
{
public:
    WaveAnimation(AnimationController &controller) : Animation(controller) {}

    void update() override;
    void run() override;
    const char *getName() const override { return "Wave"; }
};

#endif
