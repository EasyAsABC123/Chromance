#!/bin/bash
set -e

source ./build_utils.sh

HASH_FILE=".tests_build_hash"
BINARY="tests"

if check_recompile_needed "$BINARY" "$HASH_FILE"; then
    echo "Compiling Chromance Tests..."

    g++ -std=c++11 -D NATIVE_TEST -D DEBUG=1 -D USING_NEOPIXEL \
      -I src \
      -I test/mocks \
      -I src/animations \
      -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src \
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
      src/animations/HeartbeatAnimation.cpp \
      -o "$BINARY"

    echo "Compilation successful."
    update_build_hash "$HASH_FILE"
fi

echo "Running tests..."
./"$BINARY"

