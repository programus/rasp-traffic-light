#ifndef __STATE_H
#define __STATE_H

struct State {
  const char* name;
  unsigned long on_time;
  unsigned long off_time;
  unsigned long rand_time;
  const char* on_lights;
  const char* off_lights;
  int repeat;
  bool interruptable;
  bool enable_button;
  bool play_sound;
};

#endif
