#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(){setbuf(stdout,0); puts("probe running"); system("id; ls -l /dev/abyss_oracle; cat /proc/version; cat /proc/modules"); sleep(1); return 0;}
