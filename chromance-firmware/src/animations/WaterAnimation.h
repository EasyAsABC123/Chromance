#ifndef WATERANIMATION_H
#define WATERANIMATION_H

#include "Animation.h"
#include <vector>

struct WaterDrop {
    int segmentIndex;
    float position; // 0.0 (top) to 1.0 (bottom)
    float speed;
    float volume; // 0.0 to 1.0 (affects brightness/width)
};

class WaterAnimation : public Animation
{
public:
    WaterAnimation(AnimationController &controller);

    void update() override;
    void run() override;
    const char *getName() const override { return "Water Pour"; }

private:
    float segmentLevels[Constants::NUMBER_OF_SEGMENTS];
    std::vector<WaterDrop> drops;
    
    int sourceNode;
    unsigned long lastSourceChange;
    
    // Helper to find downward connected segments from a node
    // Returns number of paths found, fills result array with segment indices
    int getDownwardPaths(int nodeIndex, int resultSegments[]);
};

#endif
