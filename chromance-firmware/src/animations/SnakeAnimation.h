#ifndef SNAKEANIMATION_H
#define SNAKEANIMATION_H

#include "Animation.h"
#include <deque>

struct SnakePixel {
    int segment;
    int led;
};

class SnakeAnimation : public Animation
{
public:
    SnakeAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    bool canBePreempted() override;
    bool isFinished() override;
    const char *getName() const override { return "Snake"; }

private:
    std::deque<SnakePixel> body;
    int headSegment;
    int headLed;
    int moveDirection; // 1 or -1
    int targetNode; // Node we are moving towards
    
    int foodSegment;
    int foodLed;
    
    size_t snakeLength;
    bool finished;
    
    void spawnFood();
};

#endif
