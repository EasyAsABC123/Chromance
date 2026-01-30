#ifndef GLITCHANIMATION_H
#define GLITCHANIMATION_H

#include "Animation.h"

class GlitchAnimation : public Animation
{
public:
    GlitchAnimation(AnimationController &controller) : Animation(controller) {}

    void run() override; // One-shot trigger if needed, but update handles continuous
    void update() override;
    const char *getName() const override { return "Glitch"; }
};

#endif
