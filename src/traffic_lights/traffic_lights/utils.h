#ifndef __UTILS_H
#define __UTILS_H

#include <Arduino.h>
#include "pin_set.h"

uint8_t pin_for_light(const char light) {
  uint8_t pin = -1;
  switch (light) {
  case 'r':
    pin = RED_PIN;
    break;
  case 'y':
    pin = YELLOW_PIN;
    break;
  case 'g':
    pin = GREEN_PIN;
    break;
  case 'R':
    pin = HUMAN_RED_PIN;
    break;
  case 'G':
    pin = HUMAN_GREEN_PIN;
    break;
  }

  return pin;
}

bool is_pin_in_lights(const uint8_t pin, const char* lights) {
  for (int i = 0; lights[i]; i++) {
    uint8_t lp = pin_for_light(lights[i]);
    if (lp == pin) {
      return true;
    }
  }

  return false;
}

void turn_on_lights(const char* lights) {
  uint8_t all_lights[] = {
    RED_PIN,
    YELLOW_PIN,
    GREEN_PIN,
    HUMAN_RED_PIN,
    HUMAN_GREEN_PIN
  };

  size_t n = sizeof(all_lights) / sizeof(uint8_t);

  for (size_t i = 0; i < n; i++) {
    uint8_t light = all_lights[i];
    digitalWrite(light, is_pin_in_lights(light, lights) ? HIGH : LOW);
  }
}

void turn_off_lights(const char* lights) {
  for (int i = 0; lights[i]; i++) {
    char c = lights[i];
    uint8_t pin = pin_for_light(c);
    digitalWrite(pin, LOW);
  }
}

void enable_button(const bool isEnable, void (*handler)()) {
  if (isEnable) {
    attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), handler, FALLING);
    digitalWrite(PRESS_LIGHT_PIN, HIGH);
    digitalWrite(WAIT_LIGHT_PIN, LOW);
  } else {
    detachInterrupt(digitalPinToInterrupt(BUTTON_PIN));
    digitalWrite(PRESS_LIGHT_PIN, LOW);
    digitalWrite(WAIT_LIGHT_PIN, LOW);
  }
}

#endif
