#ifndef PLASMAANIMATION_H
#define PLASMAANIMATION_H

#include "Animation.h"

class PlasmaAnimation : public Animation
{
public:
    PlasmaAnimation(AnimationController &controller) : Animation(controller) {}

    void update() override;
    void run() override;
    const char *getName() const override { return "Plasma"; }
};

#endif
