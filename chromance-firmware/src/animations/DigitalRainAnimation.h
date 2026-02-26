#ifndef DIGITALRAINANIMATION_H
#define DIGITALRAINANIMATION_H

#include "Animation.h"
#include <vector>

struct RainDrop {
    int segment;
    float position; // 0.0 top to 1.0 bottom
    float speed;
};

class DigitalRainAnimation : public Animation
{
public:
    DigitalRainAnimation(AnimationController &controller) : Animation(controller), finished(false), startTime(0), stopping(false) {}

    void update() override;
    void run() override;
    bool canBePreempted() override;
    bool isFinished() override;
    const char *getName() const override { return "Digital Rain"; }

private:
    std::vector<RainDrop> drops;
    bool finished;
    unsigned long startTime;
    bool stopping;
};

#endif
