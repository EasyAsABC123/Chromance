CXX = g++
CXXFLAGS = -std=c++11 -D NATIVE_TEST -D DEBUG=1 -D USING_NEOPIXEL
INCLUDES = -I src \
           -I test/mocks \
           -I src/animations \
           -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src \
           -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src/src

BUILD_DIR = build
OBJ_DIR = $(BUILD_DIR)/obj

# Common source files
COMMON_SRCS = src/AnimationController.cpp \
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
              src/animations/WaterAnimation.cpp \
              src/animations/InfernoAnimation.cpp \
              src/animations/BouncingBallsAnimation.cpp \
              src/animations/FirefliesAnimation.cpp \
              src/animations/FireworksAnimation.cpp \
              src/animations/WaveAnimation.cpp

# Source files for emulator
EMULATOR_SRCS = test/test_main.cpp $(COMMON_SRCS)

# Source files for tests
TEST_SRCS = test/test_animations.cpp $(COMMON_SRCS)

# Generate object file paths
EMULATOR_OBJS = $(patsubst %.cpp,$(OBJ_DIR)/%.o,$(EMULATOR_SRCS))
TEST_OBJS = $(patsubst %.cpp,$(OBJ_DIR)/%.o,$(TEST_SRCS))

# Default target
all: emulator tests

emulator: $(EMULATOR_OBJS)
	@echo "Linking $@"
	@$(CXX) $(CXXFLAGS) $(EMULATOR_OBJS) -o $@

tests: $(TEST_OBJS)
	@echo "Linking $@"
	@$(CXX) $(CXXFLAGS) $(TEST_OBJS) -o $@

run_tests: tests
	@./tests

# Compile source to object
$(OBJ_DIR)/%.o: %.cpp
	@mkdir -p $(dir $@)
	@echo "Compiling $<"
	@$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -rf $(BUILD_DIR) emulator tests

.PHONY: all clean run_tests