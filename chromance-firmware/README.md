# Instructions

## How to build/upload

This will cover how to get this codebase up and running on your Chromance by Zack Freedman.

1. [Install VSCode](https://code.visualstudio.com/)
1. Install the [PlatformIO IDE](https://marketplace.visualstudio.com/items?itemName=platformio.platformio-ide) extension in vscode
1. Open a terminal (of your choosing) and go to the directory you want to store git repos
1. Clone this repo locally `git clone https://github.com/EasyAsABC123/Chromance.git`
1. Change directory to the cloned repo `cd Chromance`
1. Change directory to the `chromance-firmware` folder `cd chromance-firmware`
1. Open this folder in VSCode `code .` or via the VSCode UI (File -> Open Folder)
1. You should verify the contents of platformio.ini, details in How to Setup, then you will open the platformio extension and run build then upload (choose USB for initial)

## How to Setup

### platformio.ini

The following might need to be changed depending on your setup/hardware.

- Change `board = esp-wrover-kit` to match the model of ESP32 you have, a list can be [found here](https://docs.platformio.org/en/latest/boards/index.html)
- Change `upload_port = 192.168.1.90` to match the static IP you setup in your router after setting up the WiFi.

### variables.h

- Open up [variables.h](src/variables.h)
- Edit the following in `variables.h`
  - Set your LED Type to `#define __LED_TYPE NEOPIXEL` for NEOPIXEL or `#define __LED_TYPE DOTSTAR` for DOTSTAR LEDS

#### Optionally Edit the Following as needed

- `BLUE_STRIP_DATA_PIN`: With the Data Pin you are using for the blue
- `GREEN_STRIP_DATA_PIN`: With the Data Pin you are using for the green
- `RED_STRIP_DATA_PIN`: With the Data Pin you are using for the red
- `BLACK_STRIP_DATA_PIN`: With the Data Pin you are using for the black
- If using DOTSTAR LEDS
  - `BLUE_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the blue
  - `GREEN_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the red
  - `RED_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the green
  - `BLACK_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the black

## How to connect to wifi

This bad boy will create a wifi network named `Chromance` you simply need to join this network and a popup UI will guide you through joining it to your network.

Once it is on your network I recommend going into your router and assigning the mac address a static IP, to make uploading easier since you'll specify the IP in your [platformio.ini](platformio.ini) file.

## How to make an animation

To create your own animations you will want to look at the [mapping.h](src/mapping.h) file and the [ripple.cpp](src/ripple.cpp) file to a lesser extent.  This repository contains a [mapping.jpg](mapping.jpg) that shows each nodes number and the segment numbers.  You can use this image to make sense of the `nodeConnections`, `segmentConnections`, `borderNodes`, `cubeNodes`, `funNodes`, and `starburstNode` variables in [`mapping.h`](src/mapping.h)
