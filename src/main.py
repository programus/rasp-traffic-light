#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import random
import signal
import sys

RED_LIGHT_TIME = 15
YELLO_LIGHT_TIME = 1
GREEN_LIGTH_TIME = 15

RANDOM_TIME = 5

RED_PIN = 18
YELLOW_PIN = 23
GREEN_PIN = 24

def setup():
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)
  GPIO.setup([RED_PIN, YELLOW_PIN, GREEN_PIN], GPIO.OUT)
  GPIO.output([RED_PIN, YELLOW_PIN, GREEN_PIN], GPIO.LOW)

def loop():
  turn_on(GREEN_PIN, GREEN_LIGTH_TIME + random.randint(0, RANDOM_TIME)) 
  turn_on(YELLOW_PIN, YELLO_LIGHT_TIME)
  turn_on(RED_PIN, RED_LIGHT_TIME + random.randint(0, RANDOM_TIME))

def finished():
  GPIO.output([RED_PIN, YELLOW_PIN, GREEN_PIN], GPIO.LOW)

def turn_on(pin, duration):
  print 'turn on %d (%f)' % (pin, duration)
  GPIO.output(pin, GPIO.HIGH)
  time.sleep(duration)
  print 'turn off'
  GPIO.output(pin, GPIO.LOW)

def signal_handler(signal, frame):
  finished()
  sys.exit(0)

if __name__ == '__main__':
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)
  setup()
  while (True):
    loop()

