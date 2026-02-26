#ifndef INFERNOANIMATION_H
#define INFERNOANIMATION_H

#include "Animation.h"

class InfernoAnimation : public Animation
{
public:
    InfernoAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    bool canBePreempted() override;
    bool isFinished() override;
    const char *getName() const override { return "Inferno"; }

private:
    float heatPixels[Constants::NUM_OF_PIXELS];
    unsigned long startTime;
    unsigned long duration;
    bool finished;
    
    // Helper to map 0-255 heat to color
    uint32_t getHeatColor(float h);
};

#endif
