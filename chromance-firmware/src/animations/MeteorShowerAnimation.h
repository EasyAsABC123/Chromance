#ifndef METEORSHOWERANIMATION_H
#define METEORSHOWERANIMATION_H

#include "Animation.h"

class MeteorShowerAnimation : public Animation
{
public:
    MeteorShowerAnimation(AnimationController &controller) : Animation(controller) {}

    void run() override;
    const char *getName() const override { return "Meteor Shower"; }
};

#endif
