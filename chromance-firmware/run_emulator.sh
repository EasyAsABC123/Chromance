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

BINARY="emulator"

echo "Building emulator..."
if ! make emulator; then
    echo "Build failed."
    exit 1
fi

echo "Running emulator..."
./"$BINARY" "$@"
