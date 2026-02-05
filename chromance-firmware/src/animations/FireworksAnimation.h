#ifndef FIREWORKSANIMATION_H
#define FIREWORKSANIMATION_H

#include "Animation.h"

class FireworksAnimation : public Animation
{
public:
    FireworksAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    bool canBePreempted() override;
    bool isFinished() override;
    const char *getName() const override { return "Fireworks"; }

private:
    static const int MAX_FIREWORKS = 3;

    struct Firework
    {
        bool active;
        int rippleIndex;
        int targetNode;
        unsigned long duration;
        
        // Track rocket position for explosion
        int lastKnownSegment;
        int lastKnownLed;
        int lastKnownNode;
    };

    Firework fireworks[MAX_FIREWORKS];
    
    void launchFirework();
    void explodeFirework(int index);
};

#endif
