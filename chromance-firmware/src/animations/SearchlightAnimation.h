#ifndef SEARCHLIGHTANIMATION_H
#define SEARCHLIGHTANIMATION_H

#include "Animation.h"

class SearchlightAnimation : public Animation
{
public:
    SearchlightAnimation(AnimationController &controller) : Animation(controller), currentAngle(0.0f) {}

    void update() override;
    void run() override; // Needed for interface, but logic is in update
    const char *getName() const override { return "Searchlight"; }

private:
    float currentAngle;
};

#endif
