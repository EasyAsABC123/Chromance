#ifndef CONFIGURATION_H
#define CONFIGURATION_H

class Configuration
{
public:
    Configuration();

    bool isSleepEnabled() const { return sleepEnabled; }
    void setSleepEnabled(bool enabled) { sleepEnabled = enabled; }

private:
    bool sleepEnabled;
};

#endif
