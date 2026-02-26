CXX = g++
CXXFLAGS = -std=c++11 -D NATIVE_TEST -D DEBUG=1 -D USING_NEOPIXEL
INCLUDES = -I src \
           -I test/mocks \
           -I src/animations \
           -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src \
           -I .pio/libdeps/esp-wrover-kit/ArduinoJson/src/src

BUILD_DIR = build
OBJ_DIR = $(BUILD_DIR)/obj

# Find all animation source files dynamically
ANIMATION_SRCS = $(wildcard src/animations/*.cpp)

# Common source files
COMMON_SRCS = src/AnimationController.cpp \
              src/LedController.cpp \
              src/Configuration.cpp \
              src/Topology.cpp \
              src/ripple.cpp \
              $(ANIMATION_SRCS)

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

list:
	@echo "Registered Animations (Index: Name):"
	@grep -rh "REGISTER_ANIMATION" src/animations | awk -F'(' '{print $$2}' | awk -F')' '{print $$1}' | sort | uniq | cat -n | awk '{print $$1-1 ": " $$2}'

.PHONY: all clean run_tests list_animations
