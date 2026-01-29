# Legacy Setup and Configuration Notes

This document contains setup information from a previous version of the `README.md`. While much of this is covered in the main `README.md`, some details are preserved here for historical context. Please note that some information may be outdated.

## Original Pin and LED Type Configuration (Outdated)

The following instructions referred to a file named `variables.h` which no longer exists. This has been replaced by `src/Constants.h`.

### Configuring Pins and LED Type

Configuration is now done in `src/Constants.h`.

- **LED Type**: To set your LED type, comment or uncomment the relevant lines in the "LED Type Configuration" section of `src/Constants.h`.
- **Pin Definitions**: The data and clock pins for the LED strips are now defined in the "Pin Configuration" section of `src/Constants.h`.

The original instructions were:
> ### variables.h
>
> - Open up [variables.h](src/variables.h)
> - Edit the following in `variables.h`
>   - Set your LED Type to `#define __LED_TYPE NEOPIXEL` for NEOPIXEL or `#define __LED_TYPE DOTSTAR` for DOTSTAR LEDS
>
> #### Optionally Edit the Following as needed
>
> - `BLUE_STRIP_DATA_PIN`: With the Data Pin you are using for the blue
> - `GREEN_STRIP_DATA_PIN`: With the Data Pin you are using for the green
> - `RED_STRIP_DATA_PIN`: With the Data Pin you are using for the red
> - `BLACK_STRIP_DATA_PIN`: With the Data Pin you are using for the black
> - If using DOTSTAR LEDS
>   - `BLUE_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the blue
>   - `GREEN_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the red
>   - `RED_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the green
>   - `BLACK_STRIP_CLOCK_PIN`: With the Clock Pin you are using for the black

## Original Animation Creation Guide

The main `README.md` now contains a more up-to-date guide for creating animations. However, the original text provided some useful pointers to specific files and variables.

The original text was:
> To create your own animations you will want to look at the [mapping.h](src/mapping.h) file and the [ripple.cpp](src/ripple.cpp) file to a lesser extent.  This repository contains a [mapping.jpg](mapping.jpg) that shows each nodes number and the segment numbers.  You can use this image to make sense of the `nodeConnections`, `segmentConnections`, `borderNodes`, `cubeNodes`, `funNodes`, and `starburstNode` variables in [`mapping.h`](src/mapping.h)
