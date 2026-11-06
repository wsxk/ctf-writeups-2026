#include "entities.h"
#include "logging.h"
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

char name[ENTITY_NAME_SIZE];
struct Host *win_host;

void setup_chall() {
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  if (init_logging() != 0) {
    puts("Failed to init logging, if this happens on the remote please contact "
         "an admin");
    exit(1);
  }

  for (int i = 0; i < MAX_ROUTERS; i++) {
    routers[i] = NULL;
  }
  for (int i = 0; i < MAX_HOSTS; i++) {
    hosts[i] = NULL;
  }

  win_host = create_host("win_host");
  if (win_host == NULL) {
    puts("Failed to create win host");
    exit(1);
  }
  if (start_host(win_host, true) != 0) {
    puts("Failed to start win host");
    exit(1);
  }
  win_host->interface.ip[0] = 1;
  win_host->interface.ip[1] = 2;
  win_host->interface.ip[2] = 3;
  win_host->interface.ip[3] = 4;
  win_host->interface.netmask[0] = 255;
  win_host->interface.netmask[1] = 255;
  win_host->interface.netmask[2] = 255;
  win_host->interface.netmask[3] = 255;
  hosts[MAX_HOSTS] = win_host;
}

void menu() {
  printf("\n");
  printf("1. Create Host\n");
  printf("2. Create Router\n");
  printf("3. Connect Interface\n");
  printf("4. Disconnect Interface\n");
  printf("5. Delete Router\n");
  printf("6. Delete Host\n");
  printf("7. Start Router\n");
  printf("8. Start Host\n");
  printf("9. Stop Router\n");
  printf("10. Stop Host\n");
  printf("11. Turn on / off interface\n");
  printf("12. Assign IP to interface\n");
  printf("13. Add Route\n");
  printf("14. Remove Route\n");
  printf("15. Show Network\n");
  printf("16. Simulation menu\n");
  // printf("17. Show hint ;)\n");
  printf("0. Exit\n");
}

void simulation_menu() {
  printf("\n");
  printf("Current Network Status:\n");
  show_network(false);
  printf("1. Ping\n");
  printf("2. Read Logs\n");
  printf("3. Return to main menu\n");
}

int get_choice(const char *prompt) {
  int choice;
  printf("\n");
  printf("%s", prompt);
  if (scanf("%d", &choice) != 1) {
    // Clear invalid input from buffer
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
    return -1;
  }
  return choice;
}

int get_choice_with_limits(const char *prompt, int min, int max,
                           const char *error_message) {
  int choice = get_choice(prompt);
  if (choice < min || choice > max) {
    puts(error_message);
    return -1;
  } else
    return choice;
}

char *get_string(const char *prompt) {
  printf("%s", prompt);
  read(0, name, ENTITY_NAME_SIZE);
  return name;
}

char *safely_replace_newline(char *str){
  for(int i = 0; i < strlen(str); i++){
    if(str[i] == '\n'){
      str[i] = '\0';
    }
  }
  return str;
}

int main() {
  setup_chall();

  int choice, index;
  while (1) {
    menu();
    choice = get_choice("Enter your choice: ");
    switch (choice) {
    case 1:
      // Create Host
      index = get_choice("Enter host index: ");
      if (index < 0 || index >= MAX_HOSTS) {
        puts("Invalid index");
        break;
      }
      if (hosts[index] != NULL) {
        puts("Host already exists");
        break;
      }
      hosts[index] = create_host(safely_replace_newline(get_string("Enter host name: ")));
      if (hosts[index] == NULL) {
        puts("Failed to create host");
        exit(1);
      }
      if (start_host(hosts[index], false) != 0) {
        puts("Failed to start host");
        exit(1);
      }

      printf("Created and started host %s\n", hosts[index]->name);
      break;

    case 2:
      // Create Router
      index = get_choice("Enter router index: ");
      if (index < 0 || index >= MAX_ROUTERS) {
        puts("Invalid index");
        break;
      }
      if (routers[index] != NULL) {
        puts("Router already exists");
        break;
      }

      routers[index] = create_router(safely_replace_newline(get_string("Enter router name: ")));
      if (routers[index] == NULL) {
        puts("Failed to create router");
        exit(1);
      }
      if (start_router(routers[index]) != 0) {
        puts("Failed to start router");
        exit(1);
      }

      printf("Created and started router %s\n", routers[index]->name);
      break;
    case 3:
      // Connect Interface
      index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
      if (index == -1) break;
      
      struct Router *router = routers[index];
      if (router == NULL) {
        puts("Router does not exist");
        break;
      }

      int int_index = get_choice_with_limits("Enter interface index: ", 0, INTERFACE_COUNT-1, "Invalid index");
      if (int_index == -1) break;

      puts("Choose the target:");
      choice = get_choice_with_limits("Host [1] or Router [2]: ", 1, 2, "Invalid choice");
      if (choice == -1) break;
      
      struct Interface *target;
      pthread_mutex_t *target_lock = NULL;
      if (choice == 1) {
        // Host
        index = get_choice_with_limits("Insert Host index: ", 0, MAX_HOSTS-1, "Invalid index");
        if (index == -1) break;

        if(hosts[index] == NULL) {
          puts("Host does not exist");
          break;
        }
        target = &hosts[index]->interface;
      } else {
        // Router
        index = get_choice_with_limits("Insert Router index: ", 0, MAX_ROUTERS-1, "Invalid index");
        if (index == -1) break;

        
        if(routers[index] == NULL) {
          puts("Router does not exist");
          break;
        }
        
        if (routers[index] == router) {
          puts("Cannot connect to itself");
          break;
        }

        int target_int_index = get_choice_with_limits("Insert interface index: ", 0, INTERFACE_COUNT-1, "Invalid index");
        if (target_int_index == -1) break;
        
        target = &routers[index]->interfaces[target_int_index];
        target_lock = &routers[index]->interfaces_mutex;
      }

      pthread_mutex_lock(&router->interfaces_mutex);
      if (router->interfaces[int_index].connected_to != NULL) {
        puts("Interface already connected, disconnect it first.");
        pthread_mutex_unlock(&router->interfaces_mutex);
        break;
      }

      // Lock target mutex if it's a router
      if (target_lock != NULL) {
        pthread_mutex_lock(target_lock);
      }

      if (target->connected_to != NULL) {
        puts("Target's interface already connected, disconnect it first.");
        if (target_lock != NULL) {
          pthread_mutex_unlock(target_lock);
        }
        pthread_mutex_unlock(&router->interfaces_mutex);
        break;
      }

      // At this point both interfaces are locked
      router->interfaces[int_index].connected_to = target;
      target->connected_to = &router->interfaces[int_index];
      
      if (target_lock != NULL) {
        pthread_mutex_unlock(target_lock);
      }
      pthread_mutex_unlock(&router->interfaces_mutex);
      puts("Interface connected");
      break;

    case 4:
      // Disconnect Interface
      index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
      if (index == -1) break;
      
      struct Router *disc_router = routers[index];
      if (disc_router == NULL) {
        puts("Router does not exist");
        break;
      }

      int disc_int_index = get_choice_with_limits("Enter interface index: ", 0, INTERFACE_COUNT-1, "Invalid index");
      if (disc_int_index == -1) break;
      
      pthread_mutex_lock(&disc_router->interfaces_mutex);
      
      struct Interface *disc_interface = &disc_router->interfaces[disc_int_index];
      if (disc_interface->connected_to == NULL) {
        puts("Interface is not connected");
        pthread_mutex_unlock(&disc_router->interfaces_mutex);
        break;
      }

      // Get the target interface and its mutex if it's part of a router
      struct Interface *target_interface = disc_interface->connected_to;
      pthread_mutex_t *target_interface_mutex = NULL;

      if (target_interface->parent_type == PARENT_TYPE_ROUTER) {
        target_interface_mutex = &((struct Router *)target_interface->parent)->interfaces_mutex;
      }

      if (target_interface_mutex != NULL) {
          pthread_mutex_lock(target_interface_mutex);
      }

      // Disconnect both sides
      target_interface->connected_to = NULL;
      disc_interface->connected_to = NULL;
      
      if (target_interface_mutex != NULL) {
          pthread_mutex_unlock(target_interface_mutex);
      }
      pthread_mutex_unlock(&disc_router->interfaces_mutex);
      puts("Interface disconnected");
      break;

    case 5:
      // Delete Router

      index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
      if (index == -1) break;

      struct Router *del_router = routers[index];
      
      if (del_router == NULL) {
        puts("Router does not exist");
        break;
      }

      destroy_router(del_router);
      routers[index] = NULL;
      puts("Router deleted");
      break;

    case 6:
      // Delete Host

      index = get_choice_with_limits("Enter host index: ", 0, MAX_HOSTS-1, "Invalid index");
      if (index == -1) break;

      struct Host *del_host = hosts[index];
      
      if (del_host == NULL) {
        puts("Host does not exist");
        break;
      }

      destroy_host(del_host);
      hosts[index] = NULL;
      puts("Host deleted");
      break;

    case 7:
      // Start Router
      index = get_choice("Enter router index: ");
      if (index < 0 || index >= MAX_ROUTERS) {
        puts("Invalid index");
        break;
      }
      if (routers[index] == NULL) {
        puts("Router does not exist");
        break;
      }
      if (start_router(routers[index]) != 0) {
        puts("Failed to start router");
        break;
      }

      printf("Started router %s\n", routers[index]->name);
      break;

    case 8:
      // Start Host
      index = get_choice("Enter host index: ");
      if (index < 0 || index >= MAX_HOSTS) {
        puts("Invalid index");
        break;
      }
      if (hosts[index] == NULL) {
        puts("Host does not exist");
        break;
      }
      if (start_host(hosts[index], false) != 0) {
        puts("Failed to start host");
        break;
      }

      printf("Started host %s\n", hosts[index]->name);
      break;

    case 9:
      // Stop Router
      index = get_choice("Enter router index: ");
      if (index < 0 || index >= MAX_ROUTERS) {
        puts("Invalid index");
        break;
      }
      if (routers[index] == NULL) {
        puts("Router does not exist");
        break;
      }
      if (stop_router(routers[index]) != 0) {
        puts("Failed to stop router");
        exit(1);
      }
      printf("Stopped router %s\n", routers[index]->name);
      break;

    case 10:
      // Stop Host
      index = get_choice("Enter host index: ");
      if (index < 0 || index >= MAX_HOSTS) {
        puts("Invalid index");
        break;
      }
      if (hosts[index] == NULL) {
        puts("Host does not exist");
        break;
      }
      if (stop_host(hosts[index]) != 0) {
        puts("Failed to stop host");
        exit(1);
      }
      printf("Stopped host %s\n", hosts[index]->name);
      break;

    case 11:
      // Turn on/off interface
      choice = get_choice_with_limits("Router [1] or Host [2]: ", 1, 2, "Invalid choice");
      if (choice == -1) break;
      
      struct Interface *toggle_iface;
      if (choice == 1) {
        index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
        if (index == -1) break;
        if (routers[index] == NULL) {
          puts("Router does not exist");
          break;
        }
        int iface_idx = get_choice_with_limits("Enter interface index: ", 0, INTERFACE_COUNT-1, "Invalid index");
        if (iface_idx == -1) break;
        toggle_iface = &routers[index]->interfaces[iface_idx];
      } else {
        index = get_choice_with_limits("Enter host index: ", 0, MAX_HOSTS-1, "Invalid index");
        if (index == -1) break;
        if (hosts[index] == NULL) {
          puts("Host does not exist");
          break;
        }
        toggle_iface = &hosts[index]->interface;
      }
      
      toggle_iface->is_on = !toggle_iface->is_on;
      printf("Interface is now %s\n", toggle_iface->is_on ? "ON" : "OFF");
      break;

    case 12:
      // Assign IP to interface
      choice = get_choice_with_limits("Router [1] or Host [2]: ", 1, 2, "Invalid choice");
      if (choice == -1) break;
      
      struct Interface *ip_iface;
      pthread_mutex_t *ip_iface_lock = NULL;
      if (choice == 1) {
        index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
        if (index == -1) break;
        if (routers[index] == NULL) {
          puts("Router does not exist");
          break;
        }
        int iface_idx = get_choice_with_limits("Enter interface index: ", 0, INTERFACE_COUNT-1, "Invalid index");
        if (iface_idx == -1) break;
        ip_iface = &routers[index]->interfaces[iface_idx];
        ip_iface_lock = &routers[index]->interfaces_mutex;
      } else {
        index = get_choice_with_limits("Enter host index: ", 0, MAX_HOSTS-1, "Invalid index");
        if (index == -1) break;
        if (hosts[index] == NULL) {
          puts("Host does not exist");
          break;
        }
        ip_iface = &hosts[index]->interface;
      }
      
      printf("Enter IP (4 bytes, space-separated): ");
      unsigned char ip0, ip1, ip2, ip3;
      if (scanf("%hhu %hhu %hhu %hhu", &ip0, &ip1, &ip2, &ip3) != 4) {
        puts("Invalid IP format");
        int c; while ((c = getchar()) != '\n' && c != EOF);
        break;
      }
      printf("Enter netmask (4 bytes, space-separated): ");
      unsigned char nm0, nm1, nm2, nm3;
      if (scanf("%hhu %hhu %hhu %hhu", &nm0, &nm1, &nm2, &nm3) != 4) {
        puts("Invalid netmask format");
        int c; while ((c = getchar()) != '\n' && c != EOF);
        break;
      }
      
      if(ip_iface_lock != NULL) {
        pthread_mutex_lock(ip_iface_lock);
      }
      ip_iface->ip[0] = ip0;
      ip_iface->ip[1] = ip1;
      ip_iface->ip[2] = ip2;
      ip_iface->ip[3] = ip3;
      
      ip_iface->netmask[0] = nm0;
      ip_iface->netmask[1] = nm1;
      ip_iface->netmask[2] = nm2;
      ip_iface->netmask[3] = nm3;
      if(ip_iface_lock != NULL) {
        pthread_mutex_unlock(ip_iface_lock);
      }
      
      printf("IP assigned: %u.%u.%u.%u/%u.%u.%u.%u\n",
             (unsigned char)ip_iface->ip[0], (unsigned char)ip_iface->ip[1],
             (unsigned char)ip_iface->ip[2], (unsigned char)ip_iface->ip[3],
             (unsigned char)ip_iface->netmask[0], (unsigned char)ip_iface->netmask[1],
             (unsigned char)ip_iface->netmask[2], (unsigned char)ip_iface->netmask[3]);
      break;

    case 13:
      // Add Route
      index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
      if (index == -1) break;
      if (routers[index] == NULL) {
        puts("Router does not exist");
        break;
      }
      
      // Find empty route slot
      int route_slot = -1;
      pthread_mutex_lock(&routers[index]->routes_mutex);
      for (int i = 0; i < ROUTE_TABLE_SIZE; i++) {
        if (routers[index]->routes[i] == NULL) {
          route_slot = i;
          break;
        }
      }
      if (route_slot == -1) {
        puts("Route table is full");
        pthread_mutex_unlock(&routers[index]->routes_mutex);
        break;
      }
      pthread_mutex_unlock(&routers[index]->routes_mutex);
      
      printf("Enter network IP (4 bytes, space-separated): ");
      unsigned char net0, net1, net2, net3;
      if (scanf("%hhu %hhu %hhu %hhu", &net0, &net1, &net2, &net3) != 4) {
        puts("Invalid IP format");
        int c; while ((c = getchar()) != '\n' && c != EOF);
        break;
      }
      
      printf("Enter netmask (4 bytes, space-separated): ");
      unsigned char routenm0, routenm1, routenm2, routenm3;
      if (scanf("%hhu %hhu %hhu %hhu", &routenm0, &routenm1, &routenm2, &routenm3) != 4) {
        puts("Invalid netmask format");
        int c; while ((c = getchar()) != '\n' && c != EOF);
        break;
      }
      
      int out_iface = get_choice_with_limits("Enter outgoing interface index: ", 0, INTERFACE_COUNT-1, "Invalid index");
      if (out_iface == -1) break;
      
      char route_ip[IP_SIZE] = {net0, net1, net2, net3};
      char route_mask[IP_SIZE] = {routenm0, routenm1, routenm2, routenm3};
      struct Route *new_route = create_route(route_ip, route_mask, &routers[index]->interfaces[out_iface]);
      if (new_route == NULL) {
        puts("Failed to create route");
        break;
      }
      
      pthread_mutex_lock(&routers[index]->routes_mutex);
      routers[index]->routes[route_slot] = new_route;
      pthread_mutex_unlock(&routers[index]->routes_mutex);
      
      printf("Route added: %u.%u.%u.%u/%u.%u.%u.%u via eth%d\n",
             net0, net1, net2, net3, routenm0, routenm1, routenm2, routenm3, out_iface);
      break;

    case 14:
      // Remove Route
      index = get_choice_with_limits("Enter router index: ", 0, MAX_ROUTERS-1, "Invalid index");
      if (index == -1) break;
      if (routers[index] == NULL) {
        puts("Router does not exist");
        break;
      }
      
      // Show current routes
      pthread_mutex_lock(&routers[index]->routes_mutex);
      puts("Current routes:");
      for (int i = 0; i < ROUTE_TABLE_SIZE; i++) {
        if (routers[index]->routes[i] != NULL) {
          struct Route *r = routers[index]->routes[i];
          printf("  [%d] %u.%u.%u.%u/%u.%u.%u.%u\n", i,
                 (unsigned char)r->ip[0], (unsigned char)r->ip[1],
                 (unsigned char)r->ip[2], (unsigned char)r->ip[3],
                 (unsigned char)r->netmask[0], (unsigned char)r->netmask[1],
                 (unsigned char)r->netmask[2], (unsigned char)r->netmask[3]);
        }
      }
      pthread_mutex_unlock(&routers[index]->routes_mutex);
      
      int route_idx = get_choice_with_limits("Enter route index to remove: ", 0, ROUTE_TABLE_SIZE-1, "Invalid index");
      if (route_idx == -1) break;
      
      pthread_mutex_lock(&routers[index]->routes_mutex);
      if (routers[index]->routes[route_idx] == NULL) {
        puts("Route does not exist");
        pthread_mutex_unlock(&routers[index]->routes_mutex);
        break;
      }
      destroy_route(routers[index]->routes[route_idx]);
      routers[index]->routes[route_idx] = NULL;
      pthread_mutex_unlock(&routers[index]->routes_mutex);
      puts("Route removed");
      break;

    case 15:
      // Show Network
      show_network(true);
      break;

    case 16:
      // Simulation menu
      bool _continue = true;
      while(_continue) {
        simulation_menu();
        choice = get_choice("Enter your choice: ");
        switch (choice) {
          case 1:
            // Ping
            index = get_choice_with_limits("Enter Host Index: ", 0, MAX_HOSTS-1, "Invalid index");
            if (index == -1) break;
            if (hosts[index] == NULL) {
              puts("Host does not exist");
              break;
            }

            // read ip
            printf("Enter IP (4 bytes, space-separated): ");
            char ip[IP_SIZE];
            if (scanf("%hhu %hhu %hhu %hhu", &ip[0], &ip[1], &ip[2], &ip[3]) != 4) {
              puts("Invalid IP format");
              int c; while ((c = getchar()) != '\n' && c != EOF);
              break;
            }
            // Clear the newline
            int c; while ((c = getchar()) != '\n' && c != EOF);

            char data[PACKET_DATA_SIZE];
            memset(data, 0, PACKET_DATA_SIZE);
            printf("Enter data (max %d bytes): ", PACKET_DATA_SIZE);

            if (fgets(data, PACKET_DATA_SIZE, stdin) == NULL) {
              puts("Failed to read data");
              break;
            }
            char *newline = strchr(data, '\n');
            if (newline) *newline = '\0';

            reset_logging();

            struct Packet *packet = create_packet(data, hosts[index]->interface.ip, ip);
            if (memcmp(ip, hosts[index]->interface.ip, IP_SIZE) == 0) {
              send_packet_direct(&hosts[index]->interface, packet);
            } else {
              send_packet(&hosts[index]->interface, packet);
            }
            
            break;
          case 2:
            // Read Logs
            show_logs();
            break;
          case 3:
            // Return to main menu
            reset_logging();
            _continue = false;
            break;
          default:
            puts("Invalid choice");
            break;
        }
      }
      break;

    // case 17:
    //   // Show hint ;)
    //   show_hint(win_host);
    //   break;

    case 0:
      // Exit
      exit(0);
    }
  }
}
