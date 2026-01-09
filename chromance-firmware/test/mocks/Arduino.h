#ifndef ARDUINO_MOCK_H
#define ARDUINO_MOCK_H

#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <cmath>

// Types
typedef uint8_t byte;
typedef bool boolean;
typedef std::string String;

// Constants
#define OUTPUT 1
#define INPUT 0
#define HIGH 1
#define LOW 0

// Time management
namespace ArduinoMock
{
  extern unsigned long _millis;
  inline void setMillis(unsigned long m) { _millis = m; }
  inline void advanceMillis(unsigned long m) { _millis += m; }
}

inline unsigned long millis()
{
  return ArduinoMock::_millis;
}

inline void delay(unsigned long ms)
{
  ArduinoMock::advanceMillis(ms);
}

inline long random(long max)
{
  return std::rand() % max;
}

inline long random(long min, long max)
{
  return min + (std::rand() % (max - min));
}

inline void pinMode(uint8_t pin, uint8_t mode) {}
inline void digitalWrite(uint8_t pin, uint8_t val) {}
inline int digitalRead(uint8_t pin) { return 0; }

// Serial Mock
class HardwareSerial
{
public:
  void begin(unsigned long baud) {}
  void print(const char *s) { std::cout << s; }
  void print(int n) { std::cout << n; }
  void print(long n) { std::cout << n; }
  void print(double n) { std::cout << n; }
  void print(char c) { std::cout << c; }
  void println(const char *s) { std::cout << s << std::endl; }
  void println(int n) { std::cout << n << std::endl; }
  void println(long n) { std::cout << n << std::endl; }
  void println(double n) { std::cout << n << std::endl; }
  void println() { std::cout << std::endl; }

  // printf support
  template <typename... Args>
  void printf(const char *format, Args... args)
  {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), format, args...);
    std::cout << buffer;
  }
};

extern HardwareSerial Serial;

// Math
inline float constrain(float amt, float low, float high)
{
  return (amt < low) ? low : ((amt > high) ? high : amt);
}

inline long map(long x, long in_min, long in_max, long out_min, long out_max)
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

#endif // ARDUINO_MOCK_H
