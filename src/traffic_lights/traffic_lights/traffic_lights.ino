#include <Arduino.h>

#include <SD.h>                     // need to include the SD library
#include <TMRpcm.h>                 //  also need to include this library...
#include <SPI.h>

#include "State.h"
#include "pin_set.h"
#include "utils.h"

// # consts
#define BUTTON_DELAY    5000
#define BUTTON_BOUNCE   500
#define LONG_PRESS      2000

// # global variables
TMRpcm audio;   // create an object for use in this sketch
bool init_success = true;

const char* wav_files[] = {
  NULL,
  "NS-11025.WAV",
  "WE-11025.WAV"
};

State states[] = {
  // name,          on_t,   off_t, rand_t, on_l, off_l, repeat, interruptable, enable_button, play_sound
  {"all-green",       15000,  0,    3000,   "gG", "",   1, false, false,  true},
  {"blink-green",     500,    500,  0,      "gG", "G",  5, false, true,   false},
  {"human-red",       2000,   0,    0,      "gR", "",   1, false, true,   false},
  {"yellow",          1700,   0,    0,      "yR", "",   1, false, true,   false},
  {"all-red-no-int",  3000,   0,    0,      "rR", "",   1, false, true,   false},
  {"all-red",         15000,  0,    3000,   "rR", "",   1, true,  true,   false},
};

volatile byte wav_index = 0;
volatile unsigned long switch_timestamp = 0;

volatile bool button_pressed = false;
volatile unsigned long button_pressed_timestamp = 0;
char* current_file = NULL;
bool button_enabled = false;

// # setup functions
void setup_lights() {
  pinMode(RED_PIN, OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);

  pinMode(HUMAN_RED_PIN, OUTPUT);
  pinMode(HUMAN_GREEN_PIN, OUTPUT);

  pinMode(PRESS_LIGHT_PIN, OUTPUT);
  pinMode(WAIT_LIGHT_PIN, OUTPUT);
}

void setup_buttons() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  pinMode(SWITCH_BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(SWITCH_BUTTON_PIN), ctrl_wav, CHANGE);
}

bool setup_audio() {
  if (!SD.begin(SD_PIN)) {  // see if the card is present and can be initialized:
    Serial.println("SD fail");
    return false;   // don't do anything more if not
  }
  pinMode(SPEAKER_PIN, OUTPUT);
  audio.speakerPin = SPEAKER_PIN; //5,6,11 or 46 on Mega, 9 on Uno, Nano, etc
  audio.loop(1);
  wav_index = random(1, sizeof(wav_files) / sizeof(char*));

  return true;
}

void setup_serial() {
  Serial.begin(9600);
}

void setup(){
  randomSeed(analogRead(RANDOM_SEED_PIN));
  setup_serial();
  setup_lights();
  setup_buttons();
  if (setup_audio()) {
    Serial.println("ready");
  } else {
    tone(SPEAKER_PIN, 440, 2000);
    init_success = false;
  }
}

// # interruption handlers
void ctrl_wav() {
  static unsigned long last_pressed_time = 0;
  unsigned long new_time = millis();
  unsigned long dtime = new_time - switch_timestamp;
  bool pressed = !digitalRead(SWITCH_BUTTON_PIN);
  if (pressed) {
    last_pressed_time = new_time;
    if (dtime > BUTTON_BOUNCE) {
      switch_timestamp = new_time;
      byte old_index = wav_index;
      if (++wav_index >= (sizeof(wav_files) / sizeof(char*))) {
        wav_index = 1;
      }
      if (audio.isPlaying() || old_index == 0) {
        audio.play((char*) wav_files[wav_index]);
      }
    }
  } else {
    if (last_pressed_time == switch_timestamp && dtime > LONG_PRESS) {
      wav_index = 0;
      audio.disable();
    }
  }
}

void button_handler() {
  unsigned long new_time = millis();
  if (new_time - button_pressed_timestamp > BUTTON_BOUNCE) {
    button_pressed_timestamp = new_time;
    button_pressed = true;
    digitalWrite(PRESS_LIGHT_PIN, LOW);
    digitalWrite(WAIT_LIGHT_PIN, HIGH);
  }
}

// # process a state
void process_state(const State* pState) {
  Serial.println(pState->name);
  // setup button
  bool button_should_be_enabled = pState->enable_button;
  if (button_enabled != button_should_be_enabled) {
    Serial.print("enable_button: ");
    Serial.println(button_should_be_enabled);
    enable_button(button_should_be_enabled, button_handler);
    button_enabled = button_should_be_enabled;
    button_pressed = false;
  }
  // play sound
  if (pState->play_sound) {
    if (const char* fname = wav_files[wav_index]) {
      audio.play((char*) fname);
    }
  } else {
    audio.disable();
  }

  for (int i = 0; i < pState->repeat; i++) {
    turn_on_lights(pState->on_lights);
    wait(pState->on_time + random(pState->rand_time), pState->interruptable);
    if (pState->off_time) {
      turn_off_lights(pState->off_lights);
      wait(pState->off_time, pState->interruptable);
    }
  }
}

void wait(unsigned long timeout, bool interruptable) {
  Serial.print(interruptable ? "interruptable" : "block");
  Serial.print(" wait ");
  Serial.println(timeout, DEC);
  if (timeout > 0) {
    if (!interruptable) {
      delay(timeout);
    } else {
      unsigned long wait_start = millis();
      unsigned long timeout_remains;
      while (!button_pressed && (timeout_remains = wait_start + timeout - millis()) > BUTTON_DELAY) {
        Serial.println("wait button");
        delay(BUTTON_DELAY);
      }
      if (button_pressed) {
        Serial.println("interrupted!");
        unsigned long button_delay_remains = button_pressed_timestamp + BUTTON_DELAY - millis();
        if (button_delay_remains > 0x7fffffff) {
          // should be minus, but for an unsigned integer, it couldn't be
          // so set it to 0 means no wait time needed any more.
          button_delay_remains = 0;
        }
        Serial.print("button_delay_remains: ");
        Serial.println(button_delay_remains, DEC);
        Serial.print("timeout_remains: ");
        Serial.println(timeout_remains);
        unsigned long wait_time = min(button_delay_remains, timeout_remains);
        if (wait_time > 0) {
          Serial.print("wait remain: ");
          Serial.println(wait_time, DEC);
          delay(wait_time);
        }
      } else {
        delay(timeout_remains);
      }
    }
  }
}

// # the loop
void loop() {
  if (init_success) {
    size_t n = sizeof(states) / sizeof(State);
    for (size_t i = 0; i < n; i++) {
      State* pState = states + i;
      process_state(pState);
    }
  }
}
