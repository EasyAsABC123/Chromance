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
            return a.name < b.name;
        });
        return sorted;
    }

private:
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
