#ifndef CONFIGURATION_H
#define CONFIGURATION_H

#include <ArduinoJson.h>
#include <SPIFFS.h>

class AnimationController; // Forward declaration

class Configuration
{
public:
    Configuration();

    void setAnimationController(AnimationController* controller) { this->animationController = controller; }

    bool isSleepEnabled() const { return sleepEnabled; }
    void setSleepEnabled(bool enabled);

    int getRainbowBrightness() const { return rainbowBrightness; }
    void setRainbowBrightness(int brightness);

    void serialize(JsonObject &doc);
    void deserialize(const JsonObject &doc);

    void save();
    void load();

private:
    bool sleepEnabled;
    int rainbowBrightness;
    const char *configFilename = "/config.json";
    AnimationController* animationController = nullptr;
};

#endif
