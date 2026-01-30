#ifndef BOUNCINGBALLSANIMATION_H
#define BOUNCINGBALLSANIMATION_H

#include "Animation.h"
#include <vector>

struct Ball {
    int segmentIndex;
    float position; // 0.0 (top) to 1.0 (bottom)
    float velocity; // positive = down, negative = up
    uint32_t color;
    bool dying;
};

class BouncingBallsAnimation : public Animation
{
public:
    BouncingBallsAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    const char *getName() const override { return "Bouncing Balls"; }

private:
    std::vector<Ball> balls;
    
    // Helper
    int getDownwardPaths(int nodeIndex, int resultSegments[]);
    int getUpwardPaths(int nodeIndex, int resultSegments[]);
};

#endif
