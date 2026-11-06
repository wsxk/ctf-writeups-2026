#define _POSIX_C_SOURCE 200809L
#include "entities.h"
#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include "lives.h"

static struct LogBuffer log_buffer;

// Initializes the logging system.
int init_logging() {
  if (pthread_mutex_init(&log_buffer.mutex, NULL) != 0) {
    return -1;
  }

  log_buffer.is_running = true;

  if (thrd_create(&log_buffer.thread, log_thread, &log_buffer) != thrd_success) {
    return -1;
  }

  return 0;
}

// Signals log_thread to reset the logging system.
void reset_logging() {
  pthread_mutex_lock(&log_buffer.mutex);
  log_buffer.reset = true;
  pthread_mutex_unlock(&log_buffer.mutex);
  
  // Wait for log_thread to process the reset
  while (log_buffer.reset) {
    thrd_sleep(&(struct timespec){.tv_nsec = 100000000}, NULL);  // 100ms
  }
}

// Guarantees thread-safe access to the log buffer. Returns NULL if the log
// buffer is full.
struct Log *get_log() {
  if (log_buffer.index >= LOG_BUFFER_SIZE) {
    return NULL;
  }

  struct Log *log = malloc(sizeof(struct Log));
  if (!log) {
    exit(1);
  }
  memset(log, 0, sizeof(struct Log));

  log_buffer.logs[log_buffer.index++] = log;

  return log;
}

// Creates a new log entry by adding message to queue. Returns -1 if queue is full.
int log_message(char *message) {
  pthread_mutex_lock(&log_buffer.mutex);
  if (log_buffer.queue_index >= LOG_QUEUE_SIZE) {
    pthread_mutex_unlock(&log_buffer.mutex);
    return -1;
  }
  strncpy(log_buffer.queue[log_buffer.queue_index++], message, PACKET_DATA_SIZE - 1);
  pthread_mutex_unlock(&log_buffer.mutex);
  return 0;
}

void show_logs() {
  pthread_mutex_lock(&log_buffer.mutex);

  for (int i = 0; i < log_buffer.index; i++) {
    printf("%s\n", log_buffer.logs[i]->message);
  }

  pthread_mutex_unlock(&log_buffer.mutex);
}
