#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import random
import signal
import sys
import threading

RED_PIN = 17
YELLOW_PIN = 27
GREEN_PIN = 22

HUMAN_RED_PIN = 18
HUMAN_GREEN_PIN = 23

PRESS_LIGHT_PIN = 24
WAIT_LIGHT_PIN = 25

BUTTON_PIN = 4

BUTTON_DELAY_TIME = 5

pin_map = {
  'r': RED_PIN,
  'y': YELLOW_PIN,
  'g': GREEN_PIN,
  'R': HUMAN_RED_PIN,
  'G': HUMAN_GREEN_PIN,
}

states = [
  { 'name': 'all-green', 'on_time': 15, 'off_time': 0, 'repeat': 0, 'on_lights': 'gG', 'interruptable': False, 'rand_time': 3, 'enable_button': False },
  { 'name': 'blink-green', 'on_time': 0.5, 'off_time': 0.5, 'repeat': 5, 'on_lights': 'gG', 'off_lights': 'G', 'interruptable': True, 'rand_time': 0, 'enable_button': True },
  { 'name': 'human-red', 'on_time': 2, 'off_time': 0, 'repeat': 0, 'lights': 'gR', 'interruptable': False, 'rand_time': 0, 'enable_button': True },
  { 'name': 'yellow', 'on_time': 1.7, 'off_time': 0, 'repeat': 0, 'lights': 'yR', 'interruptable': False, 'rand_time': 0, 'enable_button': True },
  { 'name': 'all-red-no-interrupt', 'on_time': 3, 'off_time': 0, 'repeat': 0, 'lights': 'rR', 'interruptable': False, 'rand_time': 3, 'enable_button': True },
  { 'name': 'all-red', 'on_time': 12, 'off_time': 0, 'repeat': 0, 'lights': 'rR', 'interruptable': True, 'rand_time': 3, 'enable_button': True },
]

curr_state = None
button_event = threading.Event()
button_state = 0  # x0b - diabled, x1b - enabled, 1xb - pressed, 0xb - not pressed

def setup():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup([
      RED_PIN, 
      YELLOW_PIN,
      GREEN_PIN,
      HUMAN_GREEN_PIN,
      HUMAN_RED_PIN,
      PRESS_LIGHT_PIN,
      WAIT_LIGHT_PIN
    ],
    GPIO.OUT)
  GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.output([
      RED_PIN,
      YELLOW_PIN,
      GREEN_PIN,
      HUMAN_GREEN_PIN,
      HUMAN_RED_PIN,
      PRESS_LIGHT_PIN,
      WAIT_LIGHT_PIN
    ],
    GPIO.LOW)
  GPIO.add_interrupt_callback(
      BUTTON_PIN, 
      button_pressed, 
      edge='falling', 
      pull_up_down=GPIO.PUD_UP, 
      debounce_timeout_ms=20)

def loop():
  for state in states:
    process_state(state)

def finished():
  GPIO.cleanup()

def enable_button(enable):
  if enable:
    if button_state & 1 == 0:
      GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed, bouncetime=200)
    button_state |= 1
  else:
    if button_state & 1:
      GPIO.remove_event_detect(BUTTON_PIN)
    button_state = 0
    button_event.clear()
  update_button_light()

def update_button_light():
  GPIO.output(
      (PRESS_LIGHT_PIN, WAIT_LIGHT_PIN), 
      (button_state == 1, button_state == 3))

def button_pressed():
  time.sleep(BUTTON_DELAY_TIME)
  button_event.set()

def process_state(state):
  curr_state = state
  enable_button(state.get('enable_button'))
  all_lights, pins = zip(*pin_map.iteritems())
  for _ in xrange(max(1, state['repeat'])):
    # turn on lights
    on_lights = state['on_lights']
    GPIO.output(pins, map(lambda l: l in on_lights, all_lights))
    on_time = state['on_time'] + random.randint(0, state.get('rand_time') or 0)
    wait(state, on_time)

    # turn off lights
    off_lights = state.get('off_lights')
    if state.get('off_time'):
      GPIO.output(map(lambda l: pin_map[l], off_lights), False)
      wait(state, on_time)

def wait(state, duration):
  if state.get('interruptable'):
    button_event.wait(duration)
  else:
    time.sleep(duration)

def signal_handler(signal, frame):
  finished()
  sys.exit(0)

if __name__ == '__main__':
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)
  setup()
  while (True):
    loop()

