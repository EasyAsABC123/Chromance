#include "ShootingStarAnimation.h"
#include "../AnimationController.h"
#include "../LedController.h"
#include "../Topology.h"
#include "../Constants.h"

// Define the 7 vertical paths.
// -1 indicates a gap (invisible segment of same length).
// Path 0: Seg 12 (3->10)
// Path 1: Seg 13 (7->14) -> Seg 29 (14->19)
// Path 2: Seg 14 (4->11) -> GAP -> Seg 30 (17->22)
// Path 3: Seg 15 (8->15) -> Seg 31 (15->20)
// Path 4: Seg 16 (5->12) -> GAP -> Seg 32 (18->23)
// Path 5: Seg 17 (9->16) -> Seg 33 (16->21)
// Path 6: Seg 18 (6->13)
static const int PATHS[7][3] = {
    {12, -1, -1}, // Col 1 (Start Node 3)
    {13, 29, -1}, // Col 2 (Start Node 7)
    {14, -1, 30}, // Col 3 (Start Node 4)
    {15, 31, -1}, // Col 4 (Start Node 8)
    {16, -1, 32}, // Col 5 (Start Node 5)
    {17, 33, -1}, // Col 6 (Start Node 9)
    {18, -1, -1}  // Col 7 (Start Node 6)
};

void ShootingStarAnimation::spawnStar(ShootingStar &star)
{
  star.pathIndex = random(NUM_PATHS);
  star.distance = 0.0f;
  star.speed = 0.35f + (float)random(150) / 1000.0f; // 0.35–0.5 LEDs per frame
  star.active = true;
}

void ShootingStarAnimation::run()
{
  for (int i = 0; i < MAX_STARS; i++)
  {
    spawnStar(stars[i]);
    // Stagger starts
    // Start well above 0 so they rain down sequentially
    stars[i].distance = -(float)random(Constants::LEDS_PER_SEGMENT * 2);
  }
}

void ShootingStarAnimation::update()
{
  LedController &lc = controller.getLedController();

  for (int i = 0; i < MAX_STARS; i++)
  {
    ShootingStar &s = stars[i];
    if (!s.active)
      continue;

    // Advance
    s.distance += s.speed;
    
    // Draw Head + Trails
    // Head is at s.distance
    // Trails are at s.distance - 1, -2, -3
    // Trail falloff: 255 (head), 200, 100, 40
    struct Point
    {
      float pos;
      byte brightness;
    };
    Point points[] = {
        {s.distance, 255},
        {s.distance - 1.0f, 200},
        {s.distance - 2.0f, 100},
        {s.distance - 3.0f, 40}};

    bool pixelDrawn = false;

    for (int p = 0; p < 4; p++)
    {
      float d = points[p].pos;
      if (d < 0)
        continue; // Above top

      // Find which segment this distance falls into
      int segmentIndex = -1;
      int localLedIndex = -1;

      // Iterate through the path segments to map distance -> segment
      float localD = d;
      for (int k = 0; k < MAX_PATH_SEGMENTS; k++)
      {
        int segID = PATHS[s.pathIndex][k];
        
        // Let's check bounds
        if (localD < Constants::LEDS_PER_SEGMENT)
        {
          // It's in this block
          if (segID != -1)
          {
            segmentIndex = segID;
            // In LedController, index 0 is Floor, index 13 is Ceiling.
            // We are falling from Ceiling to Floor.
            // So localD=0 (start of segment fall) should map to Ceiling (13).
            // localD=13 (end of segment fall) should map to Floor (0).
            localLedIndex = (Constants::LEDS_PER_SEGMENT - 1) - (int)localD;
          }
          break; // Found the block (either segment or gap)
        }
        else
        {
          // Move to next block
          localD -= Constants::LEDS_PER_SEGMENT;
        }
      }

      if (segmentIndex != -1 && localLedIndex >= 0 && localLedIndex < Constants::LEDS_PER_SEGMENT)
      {
        byte b = points[p].brightness;
        lc.addPixelColor(segmentIndex, localLedIndex, b, b, b);
        pixelDrawn = true;
      }
    }

    // Check if star has fallen past the entire path
    // Max length is 3 blocks * 14 = 42.
    // Plus trail clearance (approx 4).
    if (s.distance > (MAX_PATH_SEGMENTS * Constants::LEDS_PER_SEGMENT) + 5.0f)
    {
      spawnStar(s);
    }
  }
}
