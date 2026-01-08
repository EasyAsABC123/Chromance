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

// Globals
LedController ledController;
AnimationController animationController(ledController);

const char *ntpServer = "pool.ntp.org";
const long gmtOffset_sec = -14400;
const int daylightOffset_sec = 3600;
const uint64_t TIME_TO_SLEEP = 36000;    /* Time ESP32 will go to sleep (in seconds) */
const uint64_t uS_TO_S_FACTOR = 1000000; /* Conversion factor for micro seconds to seconds */

// Task for running on Core 0
TaskHandle_t HandleArduinoOTA_Task;

// Semaphore for protecting shared variables (activeOTAUpdate, animating)
SemaphoreHandle_t animationMutex = NULL;
bool activeOTAUpdate = false;
bool animating = true;

// Function declarations
void connectToWiFi(const char *ssid, const char *pwd);
void setupOTA(void);

// Thread for running on opposite thread as loop
void HandleArduinoOTA(void *pvParameters)
{
  Serial.print("Task1 running on core ");
  Serial.println(xPortGetCoreID());

  for (;;)
  {
    ArduinoOTA.handle();

    struct tm timeinfo;
    if (!getLocalTime(&timeinfo))
    {
      Serial.println("Failed to obtain time");
      delay(500);
      continue; // Don't exit the task, just skip this iteration
    }

    if (timeinfo.tm_hour >= 22 || timeinfo.tm_hour <= 1)
    {
      // Wait for mutex to be created if setup hasn't finished yet
      if (animationMutex == NULL)
      {
        delay(100);
        continue;
      }

      // Acquire mutex to safely set activeOTAUpdate and wait for animation to stop
      if (xSemaphoreTake(animationMutex, portMAX_DELAY) == pdTRUE)
      {
        activeOTAUpdate = true;
        xSemaphoreGive(animationMutex);
      }

      // Wait for animation to complete (check with mutex protection)
      bool stillAnimating = true;
      while (stillAnimating)
      {
        if (animationMutex != NULL && xSemaphoreTake(animationMutex, portMAX_DELAY) == pdTRUE)
        {
          stillAnimating = animating;
          xSemaphoreGive(animationMutex);
        }
        if (stillAnimating)
        {
          delay(100);
        }
      }

      ledController.clear();
      ledController.show();

      esp_deep_sleep_start();
    }

    // only check for OTA update every 1/2 second
    delay(500);
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
    if (animationMutex != NULL && xSemaphoreTake(animationMutex, portMAX_DELAY) == pdTRUE)
    {
      activeOTAUpdate = true;
      xSemaphoreGive(animationMutex);
    }
    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Serial.println("Start updating " + type); });
  ArduinoOTA.onEnd([]()
                   { Serial.println("\nEnd"); });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total)
                        { Serial.printf("Progress: %u%%\r", (progress / (total / 100))); });
  ArduinoOTA.onError([](ota_error_t error)
                     {
                      // Protect shared variable access with mutex
                      if (animationMutex != NULL && xSemaphoreTake(animationMutex, portMAX_DELAY) == pdTRUE)
                      {
                        activeOTAUpdate = false;
                        xSemaphoreGive(animationMutex);
                      }
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
      HandleArduinoOTA,        /* Task function. */
      "HandleArduinoOTA_Task", /* name of task. */
      10000,                   /* Stack size of task */
      NULL,                    /* parameter of the task */
      1,                       /* priority of the task */
      &HandleArduinoOTA_Task,  /* Task handle to keep track of created task */
      0);                      /* pin task to core 0 */
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

  // Create mutex semaphore for protecting shared animation state
  animationMutex = xSemaphoreCreateMutex();
  if (animationMutex == NULL)
  {
    Serial.println("Failed to create mutex!");
  }

  ledController.begin();

  connectToWiFi();
  setupOTA();
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  esp_sleep_enable_timer_wakeup(TIME_TO_SLEEP * uS_TO_S_FACTOR);

  animationController.init();
}

void loop()
{
  // We are doing an OTA update, might as well just stop
  // Check and update with mutex protection
  bool shouldStop = false;
  if (animationMutex != NULL && xSemaphoreTake(animationMutex, portMAX_DELAY) == pdTRUE)
  {
    if (activeOTAUpdate)
    {
      animating = false;
      shouldStop = true;
    }
    xSemaphoreGive(animationMutex);
  }

  if (shouldStop)
  {
    delay(10); // Small delay to prevent tight loop
    return;
  }

  animationController.update();
}
