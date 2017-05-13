#!/usr/bin/env python

import RPi.GPIO as GPIO
import datetime
import time
import random
import signal
import sys
import threading
import os
import subprocess

RED_PIN = 17
YELLOW_PIN = 27
GREEN_PIN = 22

HUMAN_RED_PIN = 18
HUMAN_GREEN_PIN = 23

PRESS_LIGHT_PIN = 24
WAIT_LIGHT_PIN = 25

BUTTON_PIN = 4

BUTTON_DELAY_TIME = 5

SOUND_PATH = '../sounds'
SOUND_PLAYER_TERMIATE_DELAY = 0.3

NS_SOUND = 'NS.wav'
WE_SOUND = 'WE.wav'

pin_map = {
  'r': RED_PIN,
  'y': YELLOW_PIN,
  'g': GREEN_PIN,
  'R': HUMAN_RED_PIN,
  'G': HUMAN_GREEN_PIN,
}

states = [
  { 'name': 'all-green', 'on_time': 15, 'off_time': 0, 'repeat': 0, 'on_lights': 'gG', 'interruptable': False, 'rand_time': 3, 'enable_button': False, 'sound': NS_SOUND },
  { 'name': 'blink-green', 'on_time': 0.5, 'off_time': 0.5, 'repeat': 5, 'on_lights': 'gG', 'off_lights': 'G', 'interruptable': True, 'rand_time': 0, 'enable_button': True },
  { 'name': 'human-red', 'on_time': 2, 'off_time': 0, 'repeat': 0, 'on_lights': 'gR', 'interruptable': False, 'rand_time': 0, 'enable_button': True },
  { 'name': 'yellow', 'on_time': 1.7, 'off_time': 0, 'repeat': 0, 'on_lights': 'yR', 'interruptable': False, 'rand_time': 0, 'enable_button': True },
  { 'name': 'all-red-no-interrupt', 'on_time': 3, 'off_time': 0, 'repeat': 0, 'on_lights': 'rR', 'interruptable': False, 'rand_time': 0, 'enable_button': True },
  { 'name': 'all-red', 'on_time': 12, 'off_time': 0, 'repeat': 0, 'on_lights': 'rR', 'interruptable': True, 'rand_time': 3, 'enable_button': True },
]

curr_state = None
button_event = threading.Event()
button_state = 0  # x0b - diabled, x1b - enabled, 1xb - pressed, 0xb - not pressed
player_process = None

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

def loop():
  for state in states:
    process_state(state)

def finished():
  GPIO.cleanup()

def enable_button(enable):
  global button_state
  print 'enable button: %r' % enable
  if enable:
    if button_state & 1 == 0:
      GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_pressed, bouncetime=200)
      print 'added event detect'
    button_state |= 1
  else:
    if button_state & 1:
      GPIO.remove_event_detect(BUTTON_PIN)
      print 'removed event detect'
    button_state = 0
    button_event.clear()
  update_button_light()

def update_button_light():
  GPIO.output(
      (PRESS_LIGHT_PIN, WAIT_LIGHT_PIN), 
      (button_state == 1, button_state == 3))

def button_pressed(channel):
  global button_state
  print 'button pressed'
  if button_state & 2 == 0:
    print 'button state -> pressed'
    button_state |= 2
    update_button_light()
    print 'wait turn green: %fs' % BUTTON_DELAY_TIME
    time.sleep(BUTTON_DELAY_TIME)
    print 'event set'
    button_event.set()

def process_state(state):
  curr_state = state
  print state
  enable_button(state.get('enable_button'))
  play_state_sound(state)
  all_lights, pins = zip(*pin_map.iteritems())
  for _ in xrange(max(1, state['repeat'])):
    # turn on lights
    on_lights = state['on_lights']
    GPIO.output(pins, map(lambda l: l in on_lights, all_lights))
    on_time = state['on_time'] + random.randint(0, state.get('rand_time') or 0)
    print 'real on time: %f' % on_time
    wait(state, on_time)

    # turn off lights
    off_lights = state.get('off_lights')
    if state.get('off_time'):
      GPIO.output(map(lambda l: pin_map[l], off_lights), False)
      wait(state, on_time)

def play_state_sound(state):
  global player_process
  sound = state.get('sound')
  if sound:
    filepath = os.path.realpath(os.path.join(os.path.dirname(__file__), SOUND_PATH, sound))
    player_process = subprocess.Popen(['omxplayer', '--loop', filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print 'playing %s in process[%d] ...' % (filepath, player_process.pid)
  else:
    if player_process:
      player_process.stdin.write('q')
      def reset_player():
        global player_process
        if player_process.poll() is None:
          print 'terminate player'
          player_process.terminate()
        player_process = None
      threading.Timer(SOUND_PLAYER_TERMIATE_DELAY, reset_player).start()

def wait(state, duration):
  if state.get('interruptable'):
    button_event.wait(duration)
  else:
    time.sleep(duration)

def signal_handler(signal, frame):
  finished()
  sys.exit(0)

def trace(frame, event, arg):
  print "[%s] %s, %s:%d" % (datetime.datetime.now(), event, frame.f_code.co_filename, frame.f_lineno)
  return trace


if __name__ == '__main__':
  # sys.settrace(trace)
  try:
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    setup()
    while (True):
      loop()
  finally:
    finished()

