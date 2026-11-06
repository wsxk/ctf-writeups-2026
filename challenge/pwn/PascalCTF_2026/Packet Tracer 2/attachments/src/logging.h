#ifndef LOGGING_H
#define LOGGING_H

#include "entities.h"

int init_logging();
void reset_logging();
struct Log *get_log();
int log_message(char *message);
void show_logs(void);

#endif // LOGGING_H
