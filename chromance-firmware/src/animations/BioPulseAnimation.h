#ifndef BIOPULSEANIMATION_H
#define BIOPULSEANIMATION_H

#include "Animation.h"

class BioPulseAnimation : public Animation
{
public:
    BioPulseAnimation(AnimationController &controller) : Animation(controller) {}

    void update() override;
    void run() override; 
    const char *getName() const override { return "Bio Pulse"; }
};

#endif
