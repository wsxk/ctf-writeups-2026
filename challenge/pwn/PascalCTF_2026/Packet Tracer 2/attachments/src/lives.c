#include "entities.h"
#include "logging.h"
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <threads.h>
#include <time.h>

#define MESSAGE_SIZE PACKET_DATA_SIZE
const struct timespec ONE_SEC_DURATION = {1, 0}; // 1 second

int router_thread(void *arg) {
  struct Router *router = (struct Router *)arg;
  char message[MESSAGE_SIZE];

  while (router->is_running) {
    pthread_mutex_lock(&router->interfaces_mutex);
    for (int i = 0; i < INTERFACE_COUNT; i++) {
      struct Interface *interface = &router->interfaces[i];
      if (interface->is_on) {
        struct Packet *packet = receive_packet(interface);
        if (packet) {
          // if the packet is for this router
          if (memcmp(packet->destination_ip, interface->ip, IP_SIZE) == 0) {
            snprintf(message, MESSAGE_SIZE,
                     "[ROUTER %s] Received on eth%d (%u.%u.%u.%u): %u.%u.%u.%u -> %u.%u.%u.%u | %lu bytes | %s",
                     router->name, i,
                     (unsigned char)interface->ip[0], (unsigned char)interface->ip[1],
                     (unsigned char)interface->ip[2], (unsigned char)interface->ip[3],
                     (unsigned char)packet->source_ip[0], (unsigned char)packet->source_ip[1],
                     (unsigned char)packet->source_ip[2], (unsigned char)packet->source_ip[3],
                     (unsigned char)packet->destination_ip[0], (unsigned char)packet->destination_ip[1],
                     (unsigned char)packet->destination_ip[2], (unsigned char)packet->destination_ip[3],
                     strlen(packet->data), packet->data);
            log_message(message);
            free(packet);
          }
          // if the packet is for another host
          else {
            packet->ttl--;
            if (packet->ttl == 0) {
              snprintf(message, MESSAGE_SIZE,
                       "[ROUTER %s] TTL expired: %u.%u.%u.%u -> %u.%u.%u.%u | %lu bytes | %s",
                       router->name,
                       (unsigned char)packet->source_ip[0], (unsigned char)packet->source_ip[1],
                       (unsigned char)packet->source_ip[2], (unsigned char)packet->source_ip[3],
                       (unsigned char)packet->destination_ip[0], (unsigned char)packet->destination_ip[1],
                       (unsigned char)packet->destination_ip[2], (unsigned char)packet->destination_ip[3],
                       strlen(packet->data), packet->data);
              log_message(message);
              free(packet);
              continue;
            }
            bool is_for_connected_host = false;
            // check if the packet is for a host directly connected to this router
            for (int j = 0; j < INTERFACE_COUNT; j++) {
              struct Interface *connected_interface = router->interfaces[j].connected_to;
              if (connected_interface && memcmp(connected_interface->ip, packet->destination_ip, IP_SIZE) == 0) {
                send_packet(&router->interfaces[j], packet);
                snprintf(message, MESSAGE_SIZE,
                         "[ROUTER %s] Forwarded via eth%d (%u.%u.%u.%u) to connected host: %u.%u.%u.%u -> %u.%u.%u.%u | %lu bytes | %s",
                         router->name, j,
                         (unsigned char)router->interfaces[j].ip[0], (unsigned char)router->interfaces[j].ip[1],
                         (unsigned char)router->interfaces[j].ip[2], (unsigned char)router->interfaces[j].ip[3],
                         (unsigned char)packet->source_ip[0], (unsigned char)packet->source_ip[1],
                         (unsigned char)packet->source_ip[2], (unsigned char)packet->source_ip[3],
                         (unsigned char)packet->destination_ip[0], (unsigned char)packet->destination_ip[1],
                         (unsigned char)packet->destination_ip[2], (unsigned char)packet->destination_ip[3],
                         strlen(packet->data), packet->data);
                log_message(message);
                is_for_connected_host = true;
                break;
              }
            }
            // check if the packet is for a host not directly connected to this router
            if (!is_for_connected_host) {
              bool routed = false;
              pthread_mutex_lock(&router->routes_mutex);
              for(int j = 0; j < ROUTE_TABLE_SIZE; j++) {
                if (router->routes[j] == NULL) continue;
                uint32_t dest = *(uint32_t *)packet->destination_ip;
                uint32_t mask = *(uint32_t *)router->routes[j]->netmask;
                uint32_t net = *(uint32_t *)router->routes[j]->ip;
                if ((dest & mask) == (net & mask)) {
                  send_packet(router->routes[j]->interface, packet);
                  routed = true;
                  snprintf(message, MESSAGE_SIZE,
                           "[ROUTER %s] Routed via route %d (%u.%u.%u.%u): %u.%u.%u.%u -> %u.%u.%u.%u | %lu bytes | %s",
                           router->name, j,
                           (unsigned char)router->routes[j]->interface->ip[0], (unsigned char)router->routes[j]->interface->ip[1],
                           (unsigned char)router->routes[j]->interface->ip[2], (unsigned char)router->routes[j]->interface->ip[3],
                           (unsigned char)packet->source_ip[0], (unsigned char)packet->source_ip[1],
                           (unsigned char)packet->source_ip[2], (unsigned char)packet->source_ip[3],
                           (unsigned char)packet->destination_ip[0], (unsigned char)packet->destination_ip[1],
                           (unsigned char)packet->destination_ip[2], (unsigned char)packet->destination_ip[3],
                           strlen(packet->data), packet->data);
                  log_message(message);
                  break;
                }
              }
              pthread_mutex_unlock(&router->routes_mutex);
              if (!routed) {
                snprintf(message, MESSAGE_SIZE,
                         "[ROUTER %s] Dropped (no route): %u.%u.%u.%u -> %u.%u.%u.%u | %lu bytes | %s",
                         router->name,
                         (unsigned char)packet->source_ip[0], (unsigned char)packet->source_ip[1],
                         (unsigned char)packet->source_ip[2], (unsigned char)packet->source_ip[3],
                         (unsigned char)packet->destination_ip[0], (unsigned char)packet->destination_ip[1],
                         (unsigned char)packet->destination_ip[2], (unsigned char)packet->destination_ip[3],
                         strlen(packet->data), packet->data);
                log_message(message);
                free(packet);
              }
            }
          }
        }
      }
    }
    pthread_mutex_unlock(&router->interfaces_mutex);

    thrd_sleep(&ONE_SEC_DURATION, NULL);
  }

  return 0;
}

int host_thread(void *arg) {
  struct Host *host = (struct Host *)arg;
  char message[MESSAGE_SIZE];

  while (host->is_running) {
    struct Packet *packet = receive_packet(&host->interface);
    if (packet) {
      snprintf(message, MESSAGE_SIZE,
               "[HOST %s] Received on eth0 (%u.%u.%u.%u): %u.%u.%u.%u -> %u.%u.%u.%u | %lu bytes | %s",
               host->name,
               (unsigned char)host->interface.ip[0], (unsigned char)host->interface.ip[1],
               (unsigned char)host->interface.ip[2], (unsigned char)host->interface.ip[3],
               (unsigned char)packet->source_ip[0], (unsigned char)packet->source_ip[1],
               (unsigned char)packet->source_ip[2], (unsigned char)packet->source_ip[3],
               (unsigned char)packet->destination_ip[0], (unsigned char)packet->destination_ip[1],
               (unsigned char)packet->destination_ip[2], (unsigned char)packet->destination_ip[3],
               strlen(packet->data), packet->data);
      log_message(message);
      free(packet);
    }
    thrd_sleep(&ONE_SEC_DURATION, NULL);
  }

  return 0;
}

int log_thread(void *arg) {
  struct LogBuffer *log_buffer = (struct LogBuffer *)arg;
  while (log_buffer->is_running) {
    pthread_mutex_lock(&log_buffer->mutex);
    
    // Handle reset request
    if (log_buffer->reset) {
      for (int i = log_buffer->index - 1; i >= 0; i--) {
        free(log_buffer->logs[i]);
        log_buffer->logs[i] = NULL;
      }
      log_buffer->index = 0;
      
      for (int i = 0; i < log_buffer->queue_index; i++) {
        memset(log_buffer->queue[i], 0, PACKET_DATA_SIZE);
      }
      log_buffer->queue_index = 0;
      
      log_buffer->reset = false;
      pthread_mutex_unlock(&log_buffer->mutex);
      continue;
    }
    
    if (log_buffer->queue[0][0] != '\0') {
      struct Log *log = get_log();
      if (!log) {
        pthread_mutex_unlock(&log_buffer->mutex);
        continue;
      }

      strcpy(log->message, log_buffer->queue[0]);
      log->timestamp = time(NULL);
      memset(log_buffer->queue[0], 0, PACKET_DATA_SIZE);
      memmove(log_buffer->queue[0], log_buffer->queue[1], sizeof(log_buffer->queue[0]) * (LOG_QUEUE_SIZE - 1));
      memset(log_buffer->queue[LOG_QUEUE_SIZE - 1], 0, PACKET_DATA_SIZE);
      log_buffer->queue_index--;
    }
    pthread_mutex_unlock(&log_buffer->mutex);
    thrd_sleep(&ONE_SEC_DURATION, NULL);
  }

  return 0;
}

int win_host_thread(void *arg) {
  struct Host *host = (struct Host *)arg;
  char message[MESSAGE_SIZE];
  
  while (host->is_running) {
    for(int i = 0; i < MAX_ROUTERS; i++){
      if (routers[i] == NULL) continue;
      for(int j = 0; j < INTERFACE_COUNT; j++){
        struct Interface *interface = &routers[i]->interfaces[j];
        if (interface->connected_to == &host->interface) {
          const char *flag = getenv("FLAG");
          if (!flag) flag = "pascalCTF{placeholder}";
          fprintf(stderr, "%s", flag);
          exit(0);
        }
      }
    }
    thrd_sleep(&ONE_SEC_DURATION, NULL);
  }

  return 0;
}
