#ifndef FIREWORKSANIMATION_H
#define FIREWORKSANIMATION_H

#include "Animation.h"

class FireworksAnimation : public Animation
{
public:
    FireworksAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    const char *getName() const override { return "Fireworks"; }

private:
    int launchRippleIndex;
    int targetNode;
    bool exploding;
};

#endif
