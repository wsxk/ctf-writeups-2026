#include "entities.h"
#include "lives.h"
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <threads.h>
#include <string.h>

struct Router *routers[MAX_ROUTERS];
struct Host *hosts[MAX_HOSTS+1];

// Initializes a new Interface object. Returns -1 on failure.
int init_interface(struct Interface *interface, char parent_type, void *parent) {
  interface->parent_type = parent_type;
  interface->parent = parent;
  interface->is_on = true;

  if (pthread_mutex_init(&interface->buffer_mutex, NULL) != 0) {
    return -1;
  }

  return 0;
}

// Creates a new Router object along with its Interfaces.
// Returns NULL on failure.
struct Router *create_router(const char *name) {
  struct Router *router = malloc(sizeof(struct Router));
  if (!router) {
    return NULL;
  }
  memset(router, 0, sizeof(struct Router));
  router->name = strdup(name);

  if (pthread_mutex_init(&router->routes_mutex, NULL) != 0) {
    free(router->name);
    free(router);
    return NULL;
  }

  if (pthread_mutex_init(&router->interfaces_mutex, NULL) != 0) {
    pthread_mutex_destroy(&router->routes_mutex);
    free(router->name);
    free(router);
    return NULL;
  }

  for (int i = 0; i < INTERFACE_COUNT; i++) {
    if (init_interface(&router->interfaces[i], PARENT_TYPE_ROUTER, router) != 0) {
      pthread_mutex_destroy(&router->routes_mutex);
      pthread_mutex_destroy(&router->interfaces_mutex);
      free(router->name);
      free(router);
      return NULL;
    }
  }

  return router;
}

// Creates a new Host object along with its Interface. Returns NULL on failure.
struct Host *create_host(const char *name) {
  struct Host *host = malloc(sizeof(struct Host));
  if (!host) {
    return NULL;
  }
  memset(host, 0, sizeof(struct Host));
  host->name = strdup(name);

  if (init_interface(&host->interface, PARENT_TYPE_HOST, host) != 0) {
    free(host->name);
    free(host);
    return NULL;
  }
  return host;
}

// starts the router thread, returns -1 on failure, -2 if the thread is already
// running (aka the router is on)
int start_router(struct Router *router) {
  if (router->is_running) {
    return -2;
  }
  router->is_running = true;
  if (thrd_create(&router->thread, router_thread, router) != thrd_success) {
    router->is_running = false;
    return -1;
  }
  return 0;
}

// starts the host thread, returns -1 on failure, -2 if the thread is already
// running (aka the host is on)
int start_host(struct Host *host, bool is_win_host) {
  if (host->is_running) {
    return -2;
  }
  host->is_running = true;
  if (thrd_create(&host->thread, is_win_host ? win_host_thread : host_thread, host) != thrd_success) {
    host->is_running = false;
    return -1;
  }
  return 0;
}

// stops the router thread, returns -1 on failure, does nothing if the thread is
// not running (aka the router is off)
int stop_router(struct Router *router) {
  if (!router->is_running) {
    return 0;
  }

  router->is_running = false; // Signal thread to exit
  if (thrd_join(router->thread, NULL) != thrd_success) {
    return -1;
  }
  return 0;
}

// stops the host thread, returns -1 on failure, does nothing if the thread is
// not running (aka the host is off)
int stop_host(struct Host *host) {
  if (!host->is_running) {
    return 0;
  }

  host->is_running = false; // Signal thread to exit
  if (thrd_join(host->thread, NULL) != thrd_success) {
    return -1;
  }
  return 0;
}

struct Route *create_route(const char *ip, const char *netmask, struct Interface *interface) {
  struct Route *route = malloc(sizeof(struct Route));
  if (!route) {
    return NULL;
  }
  memcpy(route->ip, ip, IP_SIZE);
  memcpy(route->netmask, netmask, IP_SIZE);
  route->interface = interface;
  return route;
}

int destroy_route(struct Route *route) {
  free(route);
  return 0;
}

// Destroys an interface, it is important that it is called after the device has
// been stopped, otherwise the thread will wait indefinitely
int destroy_interface(struct Interface *interface) {
  if (interface->connected_to) {
    struct Interface *peer = interface->connected_to;
    if (peer->parent_type == PARENT_TYPE_ROUTER) {
      pthread_mutex_lock(&((struct Router *)peer->parent)->interfaces_mutex);
    }
    peer->connected_to = NULL;
    if (peer->parent_type == PARENT_TYPE_ROUTER) {
      pthread_mutex_unlock(&((struct Router *)peer->parent)->interfaces_mutex);
    }
  }

  for (int i = 0; i < INTERFACE_BUFFER_SIZE; i++) {
    if (interface->buffer[i]) {
      free(interface->buffer[i]);
    }
  }

  pthread_mutex_destroy(&interface->buffer_mutex);
  return 0;
}

int destroy_router(struct Router *router) {
  if (stop_router(router) != 0) {
    return -1;
  }

  for (int i = 0; i < INTERFACE_COUNT; i++) {
    destroy_interface(&router->interfaces[i]);
  }

  for (int i = 0; i < ROUTE_TABLE_SIZE; i++) {
    if (router->routes[i]) {
      destroy_route(router->routes[i]);
      router->routes[i] = NULL;
    }
  }
  pthread_mutex_destroy(&router->routes_mutex);
  pthread_mutex_destroy(&router->interfaces_mutex);

  free(router->name);
  free(router);
  return 0;
}

int destroy_host(struct Host *host) {
  if (stop_host(host) != 0) {
    return -1;
  }
  destroy_interface(&host->interface);
  free(host->name);
  free(host);
  return 0;
}

struct Packet *create_packet(const char *data, const char *source_ip,
                             const char *destination_ip) {
  struct Packet *packet = malloc(sizeof(struct Packet));
  if (!packet) {
    return NULL;
  }
  memset(packet, 0, sizeof(struct Packet));
  strncpy(packet->data, data, PACKET_DATA_SIZE);
  memcpy(packet->source_ip, source_ip, IP_SIZE);
  memcpy(packet->destination_ip, destination_ip, IP_SIZE);
  packet->ttl = 64;
  return packet;
}

// sends a packet to the interface connected to the provided interface, returns
// -1 if the interface is not connected or the connected interface is not on, -2
// if the receiving interface is full, 0 on success. It doesn't guarantee that
// the packet will be received by the destination interface.
int send_packet(struct Interface *interface, struct Packet *packet) {
  struct Interface *destination = interface->connected_to;

  if (!destination || !destination->is_on) {
    free(packet);
    return -1;
  }

  pthread_mutex_lock(&destination->buffer_mutex);
  if (destination->packets_in_buffer >= INTERFACE_BUFFER_SIZE) {
    pthread_mutex_unlock(&destination->buffer_mutex);
    free(packet);
    return -2;
  }
  destination->buffer[destination->index++] = packet;
  destination->packets_in_buffer++;
  pthread_mutex_unlock(&destination->buffer_mutex);
  return 0;
}

// sends a packet to the destination interface, returns -1 if the destination
// interface is not on, -2 if the destination interface is full, 0 on success.
// It doesn't guarantee that the packet will be received by the destination
// interface
int send_packet_direct(struct Interface *destination, struct Packet *packet) {
  if (!destination || !destination->is_on) {
    free(packet);
    return -1;
  }

  pthread_mutex_lock(&destination->buffer_mutex);
  if (destination->packets_in_buffer >= INTERFACE_BUFFER_SIZE) {
    pthread_mutex_unlock(&destination->buffer_mutex);
    free(packet);
    return -2;
  }
  destination->buffer[destination->index++] = packet;
  destination->packets_in_buffer++;
  pthread_mutex_unlock(&destination->buffer_mutex);
  return 0;
}

// receives a packet from the interface, returns NULL if the interface's buffer
// is empty
struct Packet *receive_packet(struct Interface *interface) {
  pthread_mutex_lock(&interface->buffer_mutex);
  if (interface->packets_in_buffer == 0) {
    pthread_mutex_unlock(&interface->buffer_mutex);
    return NULL;
  }

  struct Packet *packet = interface->buffer[0];
  memmove(interface->buffer, interface->buffer + 1,
          sizeof(struct Packet *) * (interface->packets_in_buffer - 1));
  interface->packets_in_buffer--;
  interface->index--;
  pthread_mutex_unlock(&interface->buffer_mutex);
  return packet;
}

void show_network(bool show_connections) {
  printf("\n=== NETWORK STATUS ===\n\n");
  
  // Show routers
  printf("--- ROUTERS ---\n");
  for (int i = 0; i < MAX_ROUTERS; i++) {
    if (routers[i] != NULL) {
      struct Router *r = routers[i];
      printf("[%d] %s (%s)\n", i, r->name, r->is_running ? "running" : "stopped");
      for (int j = 0; j < INTERFACE_COUNT; j++) {
        struct Interface *iface = &r->interfaces[j];
        printf("    eth%d: %u.%u.%u.%u/%u.%u.%u.%u %s",
               j,
               (unsigned char)iface->ip[0], (unsigned char)iface->ip[1],
               (unsigned char)iface->ip[2], (unsigned char)iface->ip[3],
               (unsigned char)iface->netmask[0], (unsigned char)iface->netmask[1],
               (unsigned char)iface->netmask[2], (unsigned char)iface->netmask[3],
               iface->is_on ? "[ON]" : "[OFF]");
        if (iface->connected_to) {
          if (iface->connected_to->parent_type == PARENT_TYPE_ROUTER) {
            struct Router *peer = (struct Router *)iface->connected_to->parent;
            if (show_connections){
              printf(" -> Router %s", peer->name);
            }
            else{
              printf(" [connected]");
            }
          } else {
            struct Host *peer = (struct Host *)iface->connected_to->parent;
            if (show_connections){
              printf(" -> Host %s", peer->name);
            }
            else{
              printf(" [connected]");
            }
          }
        } else {
          printf(" [disconnected]");
        }
        printf("\n");
      }
    }
  }
  
  // Show hosts
  printf("\n--- HOSTS ---\n");
  for (int i = 0; i < MAX_HOSTS+1; i++) {
    if (hosts[i] != NULL) {
      struct Host *h = hosts[i];
      struct Interface *iface = &h->interface;
      printf("[%d] %s (%s)\n", i, h->name, h->is_running ? "running" : "stopped");
      printf("    eth0: %u.%u.%u.%u/%u.%u.%u.%u %s",
             (unsigned char)iface->ip[0], (unsigned char)iface->ip[1],
             (unsigned char)iface->ip[2], (unsigned char)iface->ip[3],
             (unsigned char)iface->netmask[0], (unsigned char)iface->netmask[1],
             (unsigned char)iface->netmask[2], (unsigned char)iface->netmask[3],
             iface->is_on ? "[ON]" : "[OFF]");
      if (iface->connected_to) {
        if (iface->connected_to->parent_type == PARENT_TYPE_ROUTER) {
          struct Router *peer = (struct Router *)iface->connected_to->parent;
          if (show_connections){
            printf(" -> Router %s", peer->name);
          }
          else{
            printf(" [connected]");
          }
        } else {
          struct Host *peer = (struct Host *)iface->connected_to->parent;
          if (show_connections){
            printf(" -> Host %s", peer->name);
          }
          else{
            printf(" [connected]");
          }
        }
      } else {
        printf(" [disconnected]");
      }
      printf("\n");
    }
  }
  printf("\n");
}

// void show_hint(struct Host *win_host) {
//   puts("win_host:");
//   struct Interface *iface = &win_host->interface;
//   printf("[%d] %s (%s)\n", MAX_HOSTS, win_host->name, win_host->is_running ? "running" : "stopped");
//   printf("    eth0: %u.%u.%u.%u/%u.%u.%u.%u %s\n",
//           (unsigned char)iface->ip[0], (unsigned char)iface->ip[1],
//           (unsigned char)iface->ip[2], (unsigned char)iface->ip[3],
//           (unsigned char)iface->netmask[0], (unsigned char)iface->netmask[1],
//           (unsigned char)iface->netmask[2], (unsigned char)iface->netmask[3],
//           iface->is_on ? "[ON]" : "[OFF]");
//   printf("Host address in the heap: %p\n", win_host);
// }
