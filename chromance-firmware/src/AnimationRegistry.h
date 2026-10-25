#ifndef ANIMATION_REGISTRY_H
#define ANIMATION_REGISTRY_H

#include <vector>
#include <functional>
#include <string>
#include <algorithm>
#include <iostream>

class Animation;
class AnimationController;

using AnimationFactory = std::function<Animation*(AnimationController&)>;

struct RegistryEntry {
    std::string name;
    AnimationFactory factory;
};

class AnimationRegistry {
public:
    static AnimationRegistry& getInstance() {
        static AnimationRegistry instance;
        return instance;
    }

    void registerAnimation(const std::string& name, AnimationFactory factory) {
        entries.push_back({name, factory});
    }

    std::vector<RegistryEntry> getSortedEntries() {
        std::vector<RegistryEntry> sorted = entries;
        std::sort(sorted.begin(), sorted.end(), [](const RegistryEntry& a, const RegistryEntry& b) {
            const int aId = stableId(a.name), bId = stableId(b.name);
            return aId == bId ? a.name < b.name : aId < bId;
        });
        return sorted;
    }

private:
    // Configuration files and API clients store numeric IDs. Keep the original
    // 24 IDs and append new effects; alphabetical insertion corrupts presets.
    static int stableId(const std::string& name) {
        static const char* const names[] = {
            "BioPulseAnimation", "BouncingBallsAnimation", "CenterAnimation", "ChaseAnimation",
            "CubeAnimation", "DigitalRainAnimation", "FirefliesAnimation", "FireworksAnimation",
            "GlitchAnimation", "HeartbeatAnimation", "InfernoAnimation", "LightningAnimation",
            "MeteorShowerAnimation", "PlasmaAnimation", "RainbowAnimation", "RainbowPinwheelAnimation",
            "RainbowRadiateAnimation", "RandomAnimation", "SearchlightAnimation", "ShootingStarAnimation",
            "SnakeAnimation", "StarburstAnimation", "WaterAnimation", "WaveAnimation",
            "AuroraAnimation", "ColorWavesAnimation", "LavaLampAnimation", "NoiseDriftAnimation", "OceanWavesAnimation", "ChristmasAnimation"
        };
        const int count = sizeof(names) / sizeof(names[0]);
        for (int i = 0; i < count; ++i) if (name == names[i]) return i;
        return count;
    }
    std::vector<RegistryEntry> entries;
};

template <typename T>
class AnimationRegisterer {
public:
    AnimationRegisterer(const std::string& name) {
        AnimationRegistry::getInstance().registerAnimation(name, [](AnimationController& controller) {
            return new T(controller);
        });
    }
};

#define REGISTER_ANIMATION(ClassName) \
    static AnimationRegisterer<ClassName> global_##ClassName##_reg(#ClassName);

#endif
