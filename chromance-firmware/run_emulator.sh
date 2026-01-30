#!/bin/bash
set -e

# Help / Usage
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Chromance Emulator Runner"
    echo "Usage: ./run_emulator.sh [duration_ms] [animation_id] [time_multiplier]"
    echo "   or: ./run_emulator.sh [flags]"
    echo ""
    echo "Flags:"
    echo "  -d, --duration <ms>      Run for specified duration (default: infinite)"
    echo "  -a, --animation <id>     Force specific animation (default: auto-cycle)"
    echo "  -m, --multiplier <float> Time speed multiplier (e.g. 2.0 = 2x speed, default: 1.0)"
    echo "  -h, --help               Show this help"
    echo ""
    echo "Examples:"
    echo "  ./run_emulator.sh                    # Run normally"
    echo "  ./run_emulator.sh -m 2               # Run at 2x speed"
    echo "  ./run_emulator.sh 10000 1            # Run animation 1 for 10s"
    echo "  ./run_emulator.sh 10000 1 2.5        # Run animation 1 for 10s at 2.5x speed"
    exit 0
fi

HASH_FILE=".emulator_build_hash"
BINARY="emulator"

source ./build_utils.sh

if check_recompile_needed "$BINARY" "$HASH_FILE"; then
    echo "Compiling Chromance Emulator..."

    g++ -std=c++11 -D NATIVE_TEST -D DEBUG=1 -D USING_NEOPIXEL \
      -I src \
      -I test/mocks \
      -I src/animations \
      -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src \
      -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src/src \
      test/test_main.cpp \
      src/AnimationController.cpp \
      src/LedController.cpp \
      src/Configuration.cpp \
      src/Topology.cpp \
      src/ripple.cpp \
      src/animations/CenterAnimation.cpp \
      src/animations/ChaseAnimation.cpp \
      src/animations/CubeAnimation.cpp \
      src/animations/RainbowAnimation.cpp \
      src/animations/RandomAnimation.cpp \
      src/animations/StarburstAnimation.cpp \
      src/animations/HeartbeatAnimation.cpp \
      src/animations/RainbowPinwheelAnimation.cpp \
      src/animations/RainbowRadiateAnimation.cpp \
      src/animations/ShootingStarAnimation.cpp \
      src/animations/MeteorShowerAnimation.cpp \
      src/animations/SearchlightAnimation.cpp \
      src/animations/BioPulseAnimation.cpp \
      src/animations/GlitchAnimation.cpp \
      -o "$BINARY"

    echo "Compilation successful."
    update_build_hash "$HASH_FILE"
fi

echo "Running emulator..."
./"$BINARY" "$@"
