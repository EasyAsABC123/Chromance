#ifndef SHOOTING_STAR_ANIMATION_H
#define SHOOTING_STAR_ANIMATION_H

#include "Animation.h"
#include "../Constants.h"

struct ShootingStar
{
  int pathIndex;
  float distance; // Logical distance along the path (LEDs)
  float speed;    // LEDs per frame
  bool active;
};

class ShootingStarAnimation : public Animation
{
public:
  ShootingStarAnimation(AnimationController &controller)
      : Animation(controller, true) {}
  void run() override;
  void update() override;
  const char *getName() const override { return "Shooting Star"; }
  bool isFinished() override { return false; }

private:
  void spawnStar(ShootingStar &star);

  static const int MAX_STARS = 5;
  // 7 vertical paths. Max length is 3 segments (including gaps).
  // Segments 12, 13, 14, 15, 16, 17, 18
  static const int NUM_PATHS = 7;
  static const int MAX_PATH_SEGMENTS = 3;

  ShootingStar stars[MAX_STARS];
};

#endif

