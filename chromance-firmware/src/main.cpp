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

#include "Constants.h"
#include "LedController.h"
#include "AnimationController.h"
#include "ChromanceWebServer.h"
#include "Configuration.h"

// Globals
Configuration configuration;
LedController ledController;
AnimationController animationController(ledController);
ChromanceWebServer webServer(animationController, configuration);

const char *ntpServer = "pool.ntp.org";
const long gmtOffset_sec = -14400;
const int daylightOffset_sec = 3600;
const uint64_t TIME_TO_SLEEP = 36000;    /* Time ESP32 will go to sleep (in seconds) */
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
    if (millis() - lastTimeCheck > 2000)
    {
      lastTimeCheck = millis();
      struct tm timeinfo;
      if (!getLocalTime(&timeinfo))
      {
        Serial.println("Failed to obtain time");
        // delay(2000); // Handled by outer loop delay and timer
        continue; // Don't exit the task, just skip this iteration
      }

      if (timeinfo.tm_hour >= 22 || timeinfo.tm_hour <= 1)
      {
        if (!configuration.isSleepEnabled())
        {
          continue;
        }

        // Acquire mutex to safely set activeOTAUpdate and wait for animation to stop
        activeOTAUpdate = true;

        // Wait for animation to complete (check with mutex protection)
        bool stillAnimating = true;
        while (stillAnimating)
        {
          stillAnimating = animating;
          if (stillAnimating)
          {
            delay(1000);
          }
        }

        ledController.clear();
        ledController.show();

        Serial.println("Going to sleep now...");
        Serial.flush();

        WiFi.disconnect(true);
        WiFi.mode(WIFI_OFF);

        esp_deep_sleep_start();
      }
    }

    delay(100); // Check time every second
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

  if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_TIMER)
  {
    Serial.println("Woke up from deep sleep!");
    configuration.setSleepEnabled(true);
  }

  // Create mutex semaphore for protecting shared animation state
  ledController.begin();

  connectToWiFi();
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * uS_TO_S_FACTOR);

  animationController.init();
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
