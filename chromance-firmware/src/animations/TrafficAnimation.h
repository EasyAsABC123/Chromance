#ifndef TRAFFICANIMATION_H
#define TRAFFICANIMATION_H

#include "Animation.h"
#include <vector>

struct Car {
    int segment;
    float position;
    float speed;
    uint32_t color;
    bool waiting;
    int nextSegment;
};

class TrafficAnimation : public Animation
{
public:
    TrafficAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    bool canBePreempted() override;
    bool isFinished() override;
    const char *getName() const override { return "Traffic"; }

private:
    std::vector<Car> cars;
    bool nodeOccupied[25];
};

#endif
