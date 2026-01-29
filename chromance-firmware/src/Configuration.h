#ifndef CONFIGURATION_H
#define CONFIGURATION_H

#include <ArduinoJson.h>

class Configuration
{
public:
    Configuration();

    bool isSleepEnabled() const { return sleepEnabled; }
    void setSleepEnabled(bool enabled) { sleepEnabled = enabled; }

    int getRainbowBrightness() const { return rainbowBrightness; }
    void setRainbowBrightness(int brightness) { rainbowBrightness = brightness; }

    void serialize(JsonObject &doc);
    void deserialize(const JsonObject &doc);

private:
    bool sleepEnabled;
    int rainbowBrightness;
};

#endif
