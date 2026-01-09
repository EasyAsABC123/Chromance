#include <iostream>
#include <vector>
#include <string>
#include <cassert>
#include "Arduino.h"
#include "AnimationController.h"
#include "LedController.h"
#include "mocks/Arduino.h"
#include "Topology.h"

// Mock Definitions
namespace ArduinoMock
{
  unsigned long _millis = 0;
}
HardwareSerial Serial;

// Simple Test Framework
int tests_passed = 0;
int tests_failed = 0;

#define TEST_ASSERT(condition)                                                   \
  if (!(condition))                                                              \
  {                                                                              \
    std::cout << "FAIL: " << #condition << " at line " << __LINE__ << std::endl; \
    tests_failed++;                                                              \
  }                                                                              \
  else                                                                           \
  {                                                                              \
    tests_passed++;                                                              \
  }

#define TEST_CASE(name) \
  std::cout << "Running Test: " << name << std::endl;

void reset_mocks()
{
  ArduinoMock::_millis = 0;
  // Reset random seed if needed
  std::srand(12345);
}

void test_random_animation()
{
  TEST_CASE("RandomAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // RandomAnimation is index 0
  // It spawns a ripple randomly based on chance
  animController.startAnimation(0);

  // RandomAnimation::run() immediately starts ripples at a random node.

  // Initial state check - ripples should be active immediately
  int initial_count = animController.getActiveRippleCount();
  std::cout << "RandomAnimation Initial Ripple Count: " << initial_count << std::endl;
  TEST_ASSERT(initial_count > 0);

  // Update a few times
  for (int i = 0; i < 10; i++)
  {
    animController.update();
    ArduinoMock::advanceMillis(100);
  }

  // Should still have some ripples (lifespan is 3000ms, we advanced 1000ms)
  int count = animController.getActiveRippleCount();
  std::cout << "RandomAnimation Ripple Count after 1s: " << count << std::endl;
  TEST_ASSERT(count > 0);
}

void test_cube_animation()
{
  TEST_CASE("CubeAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // CubeAnimation is index 1
  // It spawns ripples on the cube structure (nodes 0-21)
  animController.startAnimation(1);

  // It should spawn ripples immediately or over time
  // CubeAnimation::run() iterates over nodes and starts ripples

  // Simulate one update
  animController.update();

  int count = animController.getActiveRippleCount();
  std::cout << "CubeAnimation Ripple Count: " << count << std::endl;
  TEST_ASSERT(count > 0);
}

void test_starburst_animation()
{
  TEST_CASE("StarburstAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // StarburstAnimation is index 2
  animController.startAnimation(2);

  // Starburst spawns multiple ripples from a central node
  int count = animController.getActiveRippleCount();
  std::cout << "StarburstAnimation Ripple Count: " << count << std::endl;
  TEST_ASSERT(count > 0);
}

void test_center_animation()
{
  TEST_CASE("CenterAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // CenterAnimation is index 3
  animController.startAnimation(3);

  int count = animController.getActiveRippleCount();
  std::cout << "CenterAnimation Ripple Count: " << count << std::endl;
  TEST_ASSERT(count > 0);
}

void test_rainbow_animation()
{
  TEST_CASE("RainbowAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // RainbowAnimation is index 4
  animController.startAnimation(4);

  // Force a show to update the strips from the internal buffer
  ledController.show();

  // RainbowAnimation calls ledController.rainbow() directly, it doesn't use ripples.

  int count = animController.getActiveRippleCount();
  std::cout << "RainbowAnimation Ripple Count: " << count << std::endl;
  TEST_ASSERT(count == 0);

  // Verify LEDs are lit by checking the strip directly
  // Using the helper added for NATIVE_TEST
  bool anyLit = false;
  auto strip = ledController.getStrip(0);
  if (strip)
  {
    for (int i = 0; i < strip->numPixels(); i++)
    {
      if (strip->getPixelColor(i) != 0)
      {
        anyLit = true;
        break;
      }
    }
  }

  std::cout << "RainbowAnimation LEDs Lit: " << (anyLit ? "Yes" : "No") << std::endl;
  TEST_ASSERT(anyLit);
}

void test_chase_animation()
{
  TEST_CASE("ChaseAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // ChaseAnimation is index 5
  animController.startAnimation(5);

  // Should have exactly 2 ripples initially (runner and chaser)
  int count = animController.getActiveRippleCount();
  std::cout << "ChaseAnimation Ripple Count: " << count << std::endl;
  TEST_ASSERT(count == 2);

  // Validate behaviors
  bool foundRunner = false;
  bool foundChaser = false;

  for (int i = 0; i < Constants::NUMBER_OF_RIPPLES; i++)
  {
    Ripple &r = animController.getRipple(i);
    if (r.state != STATE_DEAD)
    {
      if (r.getBehavior() == BEHAVIOR_RUNNER)
        foundRunner = true;
      if (r.getBehavior() == BEHAVIOR_CHASE)
        foundChaser = true;
    }
  }

  TEST_ASSERT(foundRunner);
  TEST_ASSERT(foundChaser);
}

void test_heartbeat_animation()
{
  TEST_CASE("HeartbeatAnimation");
  reset_mocks();

  LedController ledController;
  AnimationController animController(ledController);
  ledController.begin();
  animController.init();
  animController.setAutoSwitching(false);

  // HeartbeatAnimation is index 6
  animController.startAnimation(6);

  // Run update to set the LEDs
  animController.update();

  // Force a show to push internal buffer to the strip mock (since update() showed the *previous* frame)
  ledController.show();

  // HeartbeatAnimation uses setPixelColor directly, not ripples.
  // Check if LEDs are lit.
  bool anyLit = false;
  auto strip = ledController.getStrip(0);
  if (strip)
  {
    for (int i = 0; i < strip->numPixels(); i++)
    {
      if (strip->getPixelColor(i) != 0)
      {
        anyLit = true;
        break;
      }
    }
  }

  std::cout << "HeartbeatAnimation LEDs Lit: " << (anyLit ? "Yes" : "No") << std::endl;
  TEST_ASSERT(anyLit);
}

int main()
{
  std::cout << "Starting Animation Tests..." << std::endl;

  test_random_animation();
  test_cube_animation();
  test_starburst_animation();
  test_center_animation();
  test_rainbow_animation();
  test_chase_animation();
  test_heartbeat_animation();

  std::cout << "\nTest Summary:" << std::endl;
  std::cout << "Passed: " << tests_passed << std::endl;
  std::cout << "Failed: " << tests_failed << std::endl;

  return (tests_failed == 0) ? 0 : 1;
}
