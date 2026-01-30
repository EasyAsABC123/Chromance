#ifndef INFERNOANIMATION_H
#define INFERNOANIMATION_H

#include "Animation.h"

class InfernoAnimation : public Animation
{
public:
    InfernoAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    const char *getName() const override { return "Inferno"; }

private:
    float heat[Constants::NUMBER_OF_SEGMENTS];
    
    // Helper to map 0-255 heat to color
    uint32_t getHeatColor(float h);
};

#endif
