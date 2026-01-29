#include "Configuration.h"

Configuration::Configuration() : sleepEnabled(false), rainbowBrightness(50)
{
}

void Configuration::serialize(JsonObject &doc)
{
    doc["sleepEnabled"] = sleepEnabled;
    doc["rainbowBrightness"] = rainbowBrightness;
}

void Configuration::deserialize(const JsonObject &doc)
{
    if (doc["sleepEnabled"].is<bool>())
    {
        sleepEnabled = doc["sleepEnabled"];
    }
    if (doc["rainbowBrightness"].is<int>())
    {
        rainbowBrightness = doc["rainbowBrightness"];
    }
}
