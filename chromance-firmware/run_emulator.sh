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

# Function to calculate hash of all relevant source files
calc_hash() {
    # Find all .cpp and .h files in src and test directories
    # Sort to ensure consistent ordering
    # Calculate hash of contents to detect changes
    find src test -type f \( -name "*.cpp" -o -name "*.h" \) -print0 | sort -z | xargs -0 shasum | shasum | awk '{print $1}'
}

# Calculate current hash
CURRENT_HASH=$(calc_hash)

# Check if we need to recompile
DO_COMPILE=true

if [ -f "$BINARY" ] && [ -f "$HASH_FILE" ]; then
    STORED_HASH=$(cat "$HASH_FILE")
    if [ "$CURRENT_HASH" == "$STORED_HASH" ]; then
        DO_COMPILE=false
    fi
fi

if [ "$DO_COMPILE" = true ]; then
    echo "Compiling Chromance Emulator..."

    g++ -std=c++11 -D NATIVE_TEST -D DEBUG=1 -D USING_NEOPIXEL \
      -I src \
      -I test/mocks \
      -I src/animations \
      test/test_main.cpp \
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
      -o emulator

    echo "Compilation successful."
    echo "$CURRENT_HASH" > "$HASH_FILE"
else
    echo "Source files unchanged. Skipping compilation."
fi

echo "Running emulator..."
./emulator "$@"
