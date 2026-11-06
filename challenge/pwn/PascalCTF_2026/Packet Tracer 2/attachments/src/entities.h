#ifndef ENTITIES_H
#define ENTITIES_H

#include <pthread.h>
#include <stdbool.h>
#include <threads.h>
#include <time.h>

#define MAX_ROUTERS 5
#define MAX_HOSTS 30

#define LOG_BUFFER_SIZE 128
#define LOG_MESSAGE_SIZE 512
#define LOG_QUEUE_SIZE 8
#define PACKET_DATA_SIZE 1024
#define ENTITY_NAME_SIZE 32
#define ROUTE_TABLE_SIZE 8
#define INTERFACE_BUFFER_SIZE 8
#define INTERFACE_COUNT 4
#define IP_SIZE 4

#define PARENT_TYPE_ROUTER 1
#define PARENT_TYPE_HOST 0

struct Interface {
  struct Interface *connected_to; // needs to be NULL if not connected
  struct Packet *buffer[INTERFACE_BUFFER_SIZE];

  char is_on;
  char parent_type;
  pthread_mutex_t buffer_mutex;

  // ip stuff
  char ip[IP_SIZE];
  char netmask[IP_SIZE];

  void *parent;


  int packets_in_buffer;
  int index;
  // it is guaranteed that if packets_in_buffer < INTERFACE_BUFFER_SIZE then
  // index < INTERFACE_BUFFER_SIZE
};

struct Packet {
  char data[PACKET_DATA_SIZE];

  // routing info
  char source_ip[IP_SIZE];
  char destination_ip[IP_SIZE];

  char ttl;
};

struct Route {
  char ip[IP_SIZE];
  char netmask[IP_SIZE];
  struct Interface *interface; // this must be the Router's Interface that is
                               // connected to the next hop
};

struct Router {
  // routing stuff
  struct Interface interfaces[INTERFACE_COUNT];
  struct Route *routes[ROUTE_TABLE_SIZE];

  char *name;
  thrd_t thread;
  bool is_running;
  pthread_mutex_t routes_mutex;
  pthread_mutex_t interfaces_mutex;
};

struct Host {
  struct Interface interface;
  char *name;
  thrd_t thread;
  bool is_running;
};

struct Log {
  time_t timestamp;
  char message[LOG_MESSAGE_SIZE];
};


struct LogBuffer {
  struct Log *logs[LOG_BUFFER_SIZE];
  char queue[LOG_QUEUE_SIZE][PACKET_DATA_SIZE];
  pthread_mutex_t mutex;
  thrd_t thread;
  bool is_running;
  bool reset;
  int index;
  int queue_index;
};

// Global arrays
extern struct Router *routers[MAX_ROUTERS];
extern struct Host *hosts[MAX_HOSTS+1];
extern int router_count;
extern int host_count;

// Creation functions
int init_interface(struct Interface *interface, char parent_type, void *parent);
struct Router *create_router(const char *name);
struct Host *create_host(const char *name);
struct Route *create_route(const char *ip, const char *netmask, struct Interface *interface);
struct Packet *create_packet(const char *data, const char *source_ip,
                             const char *destination_ip);

// Thread control functions
int start_router(struct Router *router);
int start_host(struct Host *host, bool is_win_host);
int stop_router(struct Router *router);
int stop_host(struct Host *host);

// Packet functions
int send_packet(struct Interface *interface, struct Packet *packet);
int send_packet_direct(struct Interface *destination, struct Packet *packet);
struct Packet *receive_packet(struct Interface *interface);

// Destroy functions
int destroy_route(struct Route *route);
int destroy_interface(struct Interface *interface);
int destroy_router(struct Router *router);
int destroy_host(struct Host *host);

// Display functions
void show_network(bool show_connections);
// void show_hint(struct Host *win_host);

#endif // ENTITIES_H
