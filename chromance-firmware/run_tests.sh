#!/bin/bash
set -e

echo "Compiling Chromance Tests..."

g++ -std=c++11 -D NATIVE_TEST -D DEBUG=1 -D USING_NEOPIXEL \
  -I src \
  -I test/mocks \
  -I src/animations \
  test/test_animations.cpp \
  src/AnimationController.cpp \
  src/LedController.cpp \
  src/Topology.cpp \
  src/ripple.cpp \
  src/animations/CenterAnimation.cpp \
  src/animations/ChaseAnimation.cpp \
  src/animations/CubeAnimation.cpp \
  src/animations/RainbowAnimation.cpp \
  src/animations/RandomAnimation.cpp \
  src/animations/StarburstAnimation.cpp \
  -o run_tests

echo "Compilation successful. Running tests..."
./run_tests
