# Chromance Firmware

This is the official open-source firmware for the Chromance wall art by Zack Freedman. It is designed to be highly customizable, easy to develop for, and robust. It features a variety of animations, a web interface for control, and a powerful set of tools for local development and testing.

## Table of Contents
- [Architecture](#architecture)
- [Hardware Setup](#hardware-setup)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Initial Setup & Flashing](#initial-setup--flashing)
- [Development & Testing](#development--testing)
  - [Unit Tests](#unit-tests)
  - [CLI Emulator](#cli-emulator)
  - [Creating a New Animation](#creating-a-new-animation)
- [Web Interface](#web-interface)
- [Available Animations](#available-animations)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)

## Architecture

The firmware is built around a modular architecture, making it easy to understand, extend, and debug.

- **`main.cpp`**: The main entry point for the firmware. It initializes all subsystems, manages WiFi connectivity (using `WiFiManager`), handles Over-the-Air (OTA) updates, and schedules the main animation loop. It utilizes both ESP32 cores for performance, with one core dedicated to animations and the other to networking and background tasks.

- **`LedController`**: A hardware abstraction layer responsible for low-level communication with the LEDs. It abstracts the specific LED type (e.g., NeoPixel, DotStar), allowing the rest of the code to work with a simple `[segment][led]` model. It holds the color data for every LED in a buffer, which is sent to the physical strips when `show()` is called.

- **`AnimationController`**: The heart of the visual engine. It manages a collection of `Animation` objects and is responsible for:
    - Cycling through animations (automatically or manually).
    - Calling the `update()` method of the currently active animation in each loop.
    - Managing global effects like "ripples" that can be triggered by animations and travel across the LED matrix.

- **`Topology`**: This is the "map" of the Chromance hardware. It's a static class containing all the information about the physical layout, including:
    - How nodes and segments are connected.
    - The mapping of logical segments to physical LED strips.
    - Pre-defined groups of nodes (e.g., `cubeNodes`, `borderNodes`) for use in animations.

- **`ChromanceWebServer`**: Provides a web interface and a WebSocket server for real-time communication. The frontend assets (HTML, CSS, JS) are stored in **`src/WebAssets.h`** as PROGMEM strings. It allows you to:
    - Change animations.
    - Adjust settings.
    - View the status of the device.
    - Stream live LED data to a web-based emulator.

- **`Constants.h`**: Contains global compile-time configuration, including pin definitions, LED counts, and system limits. This is the primary place to adjust settings for your specific hardware setup.

- **Animations (`src/animations/`)**: Each animation is a self-contained class that inherits from the `Animation` base class. It must implement an `update()` method, which is called on every frame to update the `ledColors` buffer in the `LedController`.

## Hardware Setup

Properly powering a large number of LEDs is critical for stability. Insufficient power or inadequate wiring can lead to "brownouts," where the ESP32 resets unexpectedly, especially during bright or fast-changing animations.

For detailed instructions on wiring, power supply selection, and recommended components, please refer to the **[HARDWARE_RECOMMENDATIONS.md](HARDWARE_RECOMMENDATIONS.md)** guide.

## Getting Started

This guide will walk you through compiling and uploading the firmware to your Chromance.

### Prerequisites

1.  **VSCode**: [Install Visual Studio Code](https://code.visualstudio.com/).
2.  **PlatformIO IDE**: Install the [PlatformIO IDE extension](https://marketplace.visualstudio.com/items?itemName=platformio.platformio-ide) from the VSCode marketplace.
3.  **Git**: Ensure you have Git installed.

### Initial Setup & Flashing

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/EasyAsABC123/Chromance.git
    cd Chromance/chromance-firmware
    ```

2.  **Open in VSCode**:
    Open the `chromance-firmware` folder in VSCode.
    ```bash
    code .
    ```

3.  **Configure `platformio.ini`**:
    - **Board**: The default board is `esp-wrover-kit`. If you are using a different ESP32 board, change the `board` setting to match yours.
    - **Upload Method**:
        - For the very first flash, you must use USB. In the PlatformIO sidebar, select the `esp-wrover-kit-usb` environment.
        - For subsequent flashes, you can use Over-the-Air (OTA) updates. Select the `esp-wrover-kit` environment and update the `upload_port` with your device's IP address.

4.  **Build and Upload**:
    - Open the PlatformIO extension sidebar in VSCode.
    - Select the appropriate environment (`-usb` for the first time).
    - Click "Build" and then "Upload".

5.  **Connect to WiFi**:
    - On first boot, the device will create a WiFi network named `Chromance`.
    - Connect to this network with your phone or computer. A captive portal should appear.
    - Use the portal to select your home WiFi network and enter the password. The device will then connect to your network.
    - It is highly recommended to assign a static IP address to your Chromance via your router's settings. This makes OTA updates much easier.

## Development & Testing

This project includes powerful tools to help you develop and test animations without needing to constantly upload to the ESP32.

### Unit Tests

The project contains a suite of unit tests for the animation logic. These are compiled and run on your local machine.

To run the tests, execute the following script:
```bash
./run_tests.sh
```

### CLI Emulator

The best way to develop and debug animations is with the command-line emulator. It compiles the core animation logic natively and renders the LED output directly into your terminal using ANSI color codes.

**To run the emulator:**
```bash
./run_emulator.sh
```

**Emulator Options:**

You can pass arguments to control the emulation:

-   `./run_emulator.sh [duration_ms] [animation_id] [time_multiplier]`

| Flag | Argument | Description |
| :--- | :--- | :--- |
| `-d`, `--duration` | `<ms>` | Run the emulator for a specific duration in milliseconds. |
| `-a`, `--animation`| `<id>` | Force a specific animation to run. |
| `-m`, `--multiplier`| `<float>` | Speed up or slow down time (e.g., `2.0` for 2x speed). |

**Example:** Run the "Cube" animation (ID 1) for 10 seconds at double speed.
```bash
./run_emulator.sh -d 10000 -a 1 -m 2.0
```

### Creating a New Animation

1.  **Create the Animation File**:
    - Create a new `.h` and `.cpp` file in the `src/animations/` directory (e.g., `MyAnimation.h`, `MyAnimation.cpp`).

2.  **Define the Class**:
    - In the header file, define a class that inherits from `Animation`.
    - Implement the required virtual methods: `run()`, `update()`, and `getName()`.

    ```cpp
    // src/animations/MyAnimation.h
    #include "Animation.h"

    class MyAnimation : public Animation {
    public:
        MyAnimation(AnimationController& controller) : Animation(controller) {}
        void run() override;      // Called once when animation starts
        void update() override;   // Called every frame
        const char* getName() const override { return "My Animation"; }
    };
    ```

3.  **Implement the Logic**:
    - In the `.cpp` file, implement the `run()` and `update()` methods.
    - `run()` is typically used to reset state or trigger initial effects.
    - `update()` contains the per-frame logic (e.g., updating colors).

    ```cpp
    // src/animations/MyAnimation.cpp
    #include "MyAnimation.h"
    #include "../AnimationController.h"

    void MyAnimation::run() {
        // Initialize or reset state here
        update(); // Optional: render the first frame immediately
    }

    void MyAnimation::update() {
        // Your animation logic here
        // Example: Set the first LED of the first segment to red
        controller.getLedController().setPixelColor(0, 0, 255, 0, 0);
    }
    ```

4.  **Register the Animation**:
    - Open `src/AnimationController.cpp`.
    - Include your new animation's header file.
    - In the `AnimationController::init()` method, add your new animation to the `animations` array.

5.  **Test with the Emulator**:
    - Run `./run_emulator.sh` and pass the ID of your new animation to see it in action!

### Animation Configuration (Optional)

You can allow users to configure your animation via the web interface by overriding `getConfig` and `setConfig`.

```cpp
void getConfig(JsonObject &doc) override {
    doc["speed"] = speed;
}

void setConfig(const JsonObject &doc) override {
    if (doc["speed"].is<int>()) {
        speed = doc["speed"];
    }
}
```

## Web Interface

Once connected to your network, you can access the web interface by navigating to the device's IP address in a web browser. The interface allows for real-time control of animations and settings.

## Available Animations

The firmware comes with a variety of built-in animations:

- Random
- Cube
- Starburst
- Center
- Rainbow
- Chase
- Heartbeat
- Rainbow Pinwheel
- Rainbow Radiate
- Shooting Star

## Advanced Configuration

For details on the original setup process, including pin configurations from earlier versions of the firmware, please see the [Legacy Setup Guide](docs/Legacy_Setup.md).

## Troubleshooting

- **Flickering or Device Resets**: This is almost always a power supply issue (a "brownout"). The LEDs are drawing more current than the power supply can provide, causing the voltage to drop and the ESP32 to reset.
  - **Solution**: Carefully review and follow the **[HARDWARE_RECOMMENDATIONS.md](HARDWARE_RECOMMENDATIONS.md)** guide. Ensure you have a sufficiently rated power supply, a large capacitor, and proper wiring.