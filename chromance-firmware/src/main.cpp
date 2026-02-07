/*
   Chromance wall hexagon source (emotion controlled w/ EmotiBit)
   Partially cribbed from the DotStar example
   I smooshed in the ESP32 BasicOTA sketch, too

   (C) Voidstar Lab 2021
*/

#include <Arduino.h>
#include <WiFi.h>
#include "time.h"
#include <ESPmDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <WiFiManager.h> //https://github.com/tzapu/WiFiManager WiFi Configuration Magic
#include <SPIFFS.h>

#include "Constants.h"
#include "LedController.h"
#include "AnimationController.h"
#include "ChromanceWebServer.h"
#include "Configuration.h"

// Globals
Configuration configuration;
LedController ledController;
AnimationController animationController(ledController, configuration);
ChromanceWebServer webServer(animationController, configuration);

const char *ntpServer = "pool.ntp.org";
const long gmtOffset_sec = -18000;       // EST is UTC-5 (-5 * 3600)
const int daylightOffset_sec = 3600;     // Daylight saving offset is 1 hour
const uint64_t uS_TO_S_FACTOR = 1000000; /* Conversion factor for micro seconds to seconds */

// Task for running on Core 0
TaskHandle_t Core0TaskHandle;

// Semaphore for protecting shared variables (activeOTAUpdate, animating)
volatile bool activeOTAUpdate = false;
volatile bool animating = true;

// Function declarations
void connectToWiFi();
void setupOTA(void);

// Thread for running on opposite thread as loop
void Core0Task(void *pvParameters)
{
  Serial.print("Task1 running on core ");
  Serial.println(xPortGetCoreID());

  for (;;)
  {
    ArduinoOTA.handle();
    webServer.broadcastLedData();

    static unsigned long lastTimeCheck = 0;
    // Check the time every 2 seconds
    if (millis() - lastTimeCheck > 2000)
    {
      lastTimeCheck = millis();
      struct tm timeinfo;
      if (!getLocalTime(&timeinfo))
      {
        Serial.println("Failed to obtain time");
        continue;
      }

      // Sleep between 10pm and 8am
      if (timeinfo.tm_hour >= 22 || timeinfo.tm_hour < 8)
      {
        if (!configuration.isSleepEnabled())
        {
          continue;
        }

        // Stop animations before sleeping
        activeOTAUpdate = true;
        bool stillAnimating = true;
        while (stillAnimating)
        {
          stillAnimating = animating;
          if (stillAnimating)
          {
            delay(100);
          }
        }

        // Calculate sleep duration to wake up at 8am
        time_t now = time(nullptr);
        struct tm wakeup_time_info = timeinfo;
        wakeup_time_info.tm_hour = 8;
        wakeup_time_info.tm_min = 0;
        wakeup_time_info.tm_sec = 0;

        // If current time is past 8am, the wakeup is tomorrow
        if (timeinfo.tm_hour >= 8)
        {
          wakeup_time_info.tm_mday += 1;
        }

        time_t wakeup_t = mktime(&wakeup_time_info);
        double sleep_seconds = difftime(wakeup_t, now);
        uint64_t sleep_us = (uint64_t)(sleep_seconds * uS_TO_S_FACTOR);

        Serial.printf("Current time: %s", asctime(&timeinfo));
        Serial.printf("Wakeup time:  %s", asctime(&wakeup_time_info));
        Serial.printf("Going to sleep for %.f seconds.\n", sleep_seconds);

        esp_sleep_enable_timer_wakeup(sleep_us);
        // Enable wakeup from deep sleep on Button press (GPIO 0, Active Low)
        esp_sleep_enable_ext0_wakeup(GPIO_NUM_0, 0);

        ledController.clear();
        ledController.show();

        Serial.println("Going to sleep now...");
        Serial.flush();

        WiFi.disconnect(true);
        WiFi.mode(WIFI_OFF);

        esp_deep_sleep_start();
      }
    }

    delay(100);
  }
}

void setupOTA()
{
  // Start OTA server.
  ArduinoOTA.setHostname(Constants::HOSTNAME);
  ArduinoOTA.setPassword("esp32password");

  ArduinoOTA
      .onStart([]()
               {
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH)
      type = "sketch";
    else // U_SPIFFS
      type = "filesystem";

    // Protect shared variable access with mutex
    activeOTAUpdate = true;
    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type); });
  ArduinoOTA.onEnd([]()
                   { Serial.println("\nEnd"); });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total)
                        { Serial.printf("Progress: %u%%\r", (progress / (total / 100))); });
  ArduinoOTA.onError([](ota_error_t error)
                     {
                      // Protect shared variable access with mutex
                      activeOTAUpdate = false;
                      Serial.printf("Error[%u]: ", error);
                      if (error == OTA_AUTH_ERROR)
                        Serial.println("Auth Failed");
                      else if (error == OTA_BEGIN_ERROR)
                        Serial.println("Begin Failed");
                      else if (error == OTA_CONNECT_ERROR)
                        Serial.println("Connect Failed");
                      else if (error == OTA_RECEIVE_ERROR)
                        Serial.println("Receive Failed");
                      else if (error == OTA_END_ERROR)
                        Serial.println("End Failed"); });

  ArduinoOTA.setMdnsEnabled(true);
  ArduinoOTA.setRebootOnSuccess(true);
  delay(500);
  ArduinoOTA.begin();

  // loop and setup are pinned to core 1
  xTaskCreatePinnedToCore(
      Core0Task,        /* Task function. */
      "Core0Task",      /* name of task. */
      16384,            /* Stack size of task */
      NULL,             /* parameter of the task */
      1,                /* priority of the task */
      &Core0TaskHandle, /* Task handle to keep track of created task */
      0);               /* pin task to core 0 */
}

void connectToWiFi()
{
  WiFi.mode(WIFI_STA);
  // Check if already connected (simple check, though WiFiManager handles auto-reconnect)
  if (WiFi.status() == WL_CONNECTED)
    return;

  WiFiManager wifiManager;
  wifiManager.setWiFiAutoReconnect(true);
  wifiManager.autoConnect(Constants::HOSTNAME);
  Serial.printf("WiFi connected! IP address: %s\n", WiFi.localIP().toString().c_str());
}

void setup()
{
  Serial.begin(115200);
  Serial.println("*** LET'S GOOOOO ***");

  // Mount SPIFFS
  if (!SPIFFS.begin(true))
  {
    Serial.println("An Error has occurred while mounting SPIFFS");
  }

  // Create mutex semaphore for protecting shared animation state
  ledController.begin();

  connectToWiFi();
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);

  animationController.init();

  // Load configuration from flash
  configuration.setAnimationController(&animationController);
  configuration.load();

  // Check wakeup cause
  esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
  if (wakeup_reason == ESP_SLEEP_WAKEUP_TIMER)
  {
    Serial.println("Woke up from deep sleep (Timer)!");
    // Ensure sleep remains enabled
    configuration.setSleepEnabled(true);
  }
  else if (wakeup_reason == ESP_SLEEP_WAKEUP_EXT0)
  {
    Serial.println("Woke up from button press!");
    // Disable sleep
    configuration.setSleepEnabled(false);
  }

  webServer.begin();

  setupOTA();
}

void loop()
{
  // We are doing an OTA update, might as well just stop
  // Check and update with mutex protection
  bool shouldStop = false;
  if (activeOTAUpdate)
  {
    animating = false;
    shouldStop = true;
  }

  if (shouldStop)
  {
    delay(10); // Small delay to prevent tight loop
    return;
  }

  animationController.update();
  // webServer.broadcastLedData(); // Moved to Core 0
}
