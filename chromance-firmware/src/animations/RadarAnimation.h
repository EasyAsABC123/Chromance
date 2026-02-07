#ifndef RADARANIMATION_H
#define RADARANIMATION_H

#include "Animation.h"

class RadarAnimation : public Animation
{
public:
    RadarAnimation(AnimationController &controller) : Animation(controller), angle(0.0f) {}

    void update() override;
    void run() override;
    bool canBePreempted() override;
    bool isFinished() override;
    const char *getName() const override { return "Radar"; }

private:
    float angle;
    float nodeBrightness[25];
};

#endif
