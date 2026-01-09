#include <iostream>
#include <thread>
#include <chrono>
#include <vector>
#include <cmath>
#include <ctime>
#include <iomanip>
#include <sstream>
#include "Arduino.h"
#include "AnimationController.h"
#include "LedController.h"
#include "mocks/Arduino.h"
#include "Topology.h"

namespace ArduinoMock
{
  unsigned long _millis = 0;
}

HardwareSerial Serial;

struct Point
{
  int x;
  int y;
};

// Map of Node ID to approximate (x, y) coordinates for visualization
// Scaled for terminal (X ~ 0-80, Y ~ 0-25)
Point getNodePos(int n)
{
  switch (n)
  {
  // Top
  case 0:
    return {20, 1};
  case 1:
    return {40, 1};
  case 2:
    return {60, 1};

  // Second Row
  case 3:
    return {10, 4};
  case 4:
    return {30, 4};
  case 5:
    return {50, 4};
  case 6:
    return {70, 4};

  // Third Row
  case 7:
    return {20, 7};
  case 8:
    return {40, 7};
  case 9:
    return {60, 7};

  // Fourth Row
  case 10:
    return {10, 10};
  case 11:
    return {30, 10};
  case 12:
    return {50, 10};
  case 13:
    return {70, 10};

  // Fifth Row
  case 14:
    return {20, 13};
  case 15:
    return {40, 13};
  case 16:
    return {60, 13};

  // Sixth Row
  case 17:
    return {30, 16};
  case 18:
    return {50, 16};

  // Seventh Row
  case 19:
    return {20, 17};
  case 20:
    return {40, 17};
  case 21:
    return {60, 17};

  // Eighth Row
  case 22:
    return {30, 20};
  case 23:
    return {50, 20};

  // Bottom
  case 24:
    return {40, 23};

  default:
    return {0, 0};
  }
}

struct Pixel
{
  char ch;
  uint8_t r, g, b;
};

std::string getAnimationName(int id)
{
  switch (id)
  {
  case 0:
    return "Random";
  case 1:
    return "Cube";
  case 2:
    return "Starburst";
  case 3:
    return "Center";
  case 4:
    return "Rainbow";
  case 5:
    return "Chase";
  case 6:
    return "Heartbeat";
  case 255:
    return "None";
  default:
    return "Unknown (" + std::to_string(id) + ")";
  }
}

void printDisplay(LedController &ledController, AnimationController &animController)
{
  // Canvas size
  const int WIDTH = 80;
  const int HEIGHT = 26;
  std::vector<std::vector<Pixel>> canvas(HEIGHT, std::vector<Pixel>(WIDTH, {' ', 0, 0, 0}));

  // Draw Segments
  for (int s = 0; s < Constants::NUMBER_OF_SEGMENTS; s++)
  {
    int nodeA = Topology::segmentConnections[s][0];
    int nodeB = Topology::segmentConnections[s][1];

    Point pA = getNodePos(nodeA);
    Point pB = getNodePos(nodeB);

    // Interpolate LEDs
    for (int i = 0; i < Constants::LEDS_PER_SEGMENT; i++)
    {
      float t = (float)i / (Constants::LEDS_PER_SEGMENT - 1);
      int x = pB.x + (pA.x - pB.x) * t;
      int y = pB.y + (pA.y - pB.y) * t;

      if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT)
      {
        byte r = ledController.ledColors[s][i][0];
        byte g = ledController.ledColors[s][i][1];
        byte b = ledController.ledColors[s][i][2];

        // If LED is lit, use block char, else use a faint dot or line char
        if (r > 10 || g > 10 || b > 10)
        {
          canvas[y][x] = {'*', r, g, b}; // 'O' or '*' for lit LED
        }
        else
        {
          // Use data line color for unlit segment path
          if (canvas[y][x].ch == ' ')
          {
            int stripIdx = Topology::ledAssignments[s][0];
            uint8_t dimR = 0, dimG = 0, dimB = 0;

            switch (stripIdx)
            {
            case Constants::RED_INDEX:
              dimR = 60;
              break;
            case Constants::GREEN_INDEX:
              dimG = 60;
              break;
            case Constants::BLUE_INDEX:
              dimB = 60;
              break;
            case Constants::BLACK_INDEX:
              dimR = 40;
              dimG = 40;
              dimB = 40;
              break;
            }

            canvas[y][x] = {'.', dimR, dimG, dimB};
          }
        }
      }
    }
  }

  // Draw Nodes (optional, purely visual markers)
  for (int n = 0; n < Constants::NUMBER_OF_NODES; n++)
  {
    Point p = getNodePos(n);
    if (p.x >= 0 && p.x < WIDTH && p.y >= 0 && p.y < HEIGHT)
    {
      // White box for nodes
      canvas[p.y][p.x] = {'#', 255, 255, 255};
    }
  }

  // Buffer output to reduce flickering
  std::stringstream ss;
  ss << "\033[H"; // Move cursor to home
  ss << "Chromance Emulator (Time: " << millis() << "ms)" << "\n";
  ss << "Animation: " << getAnimationName(animController.getCurrentAnimation())
     << " | Active Ripples: " << animController.getActiveRippleCount() << "\n";

  for (int y = 0; y < HEIGHT; y++)
  {
    for (int x = 0; x < WIDTH; x++)
    {
      Pixel p = canvas[y][x];
      if (p.ch == ' ')
      {
        ss << " ";
      }
      else
      {
        // ANSI Color
        ss << "\033[38;2;" << (int)p.r << ";" << (int)p.g << ";" << (int)p.b << "m" << p.ch << "\033[0m";
      }
    }
    ss << "\n";
  }
  ss << "\033[J"; // Clear rest of screen
  std::cout << ss.str() << std::flush;
}

int main(int argc, char *argv[])
{
  long duration = 0;
  bool durationSet = false;
  int forceAnimation = -1;
  bool animationSet = false;
  float timeSpeed = 1.0f;
  bool speedSet = false;

  std::vector<std::string> positionalArgs;
  for (int i = 1; i < argc; ++i)
  {
    std::string arg = argv[i];
    if (arg == "-m" || arg == "--multiplier" || arg == "--speed")
    {
      if (i + 1 < argc)
      {
        timeSpeed = std::stof(argv[++i]);
        speedSet = true;
      }
    }
    else if (arg == "-d" || arg == "--duration")
    {
      if (i + 1 < argc)
      {
        duration = std::stol(argv[++i]);
        durationSet = true;
      }
    }
    else if (arg == "-a" || arg == "--animation")
    {
      if (i + 1 < argc)
      {
        forceAnimation = std::stoi(argv[++i]);
        animationSet = true;
      }
    }
    else
    {
      positionalArgs.push_back(arg);
    }
  }

  if (!durationSet && positionalArgs.size() > 0)
    duration = std::stol(positionalArgs[0]);
  if (!animationSet && positionalArgs.size() > 1)
    forceAnimation = std::stoi(positionalArgs[1]);
  if (!speedSet && positionalArgs.size() > 2)
    timeSpeed = std::stof(positionalArgs[2]);

  std::cout << "Starting Chromance Test Suite..." << std::endl;
  if (duration > 0)
    std::cout << "Running for " << duration << " ms" << std::endl;
  if (forceAnimation >= 0)
    std::cout << "Forcing animation " << forceAnimation << " (" << getAnimationName(forceAnimation) << ")" << std::endl;
  if (timeSpeed != 1.0f)
    std::cout << "Time multiplier: " << timeSpeed << "x" << std::endl;

  LedController ledController;
  AnimationController animationController(ledController);

  // Setup
  std::srand(std::time(0));
  ledController.begin();
  animationController.init();

  if (forceAnimation >= 0)
  {
    animationController.setAutoSwitching(false);
    animationController.startAnimation(forceAnimation);
  }
  else
  {
    // Fast forward for random mode
    ArduinoMock::advanceMillis(2000);
  }

  // Loop
  int frames = 0;
  unsigned long startMillis = millis();

  // Hide cursor
  std::cout << "\033[?25l" << std::flush;

  while (true)
  {
    if (duration > 0 && (millis() - startMillis > duration))
    {
      break;
    }

    animationController.update();

    // Visualize
    if (frames % 2 == 0)
    { // 15fps update rate for terminal
      printDisplay(ledController, animationController);
    }
    frames++;

    // Advance time
    ArduinoMock::advanceMillis((unsigned long)(33 * timeSpeed)); // ~30fps
    std::this_thread::sleep_for(std::chrono::milliseconds(33));
  }

  // Show cursor again
  std::cout << "\033[?25h" << std::endl;

  return 0;
}
