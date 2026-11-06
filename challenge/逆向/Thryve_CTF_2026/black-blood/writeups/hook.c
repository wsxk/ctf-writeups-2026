#define _GNU_SOURCE
#include <link.h>
#include <stdio.h>
#include <stdint.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
static int cb(struct dl_phdr_info *i,size_t s,void*d){
 if (!i->dlpi_name || !*i->dlpi_name) fprintf(stderr,"BASE=%p G10=%#lx G18=%#lx\n",(void*)i->dlpi_addr,*(uint64_t*)(i->dlpi_addr+0x14010),*(uint64_t*)(i->dlpi_addr+0x14018));
 return 0;
}
char *getenv(const char *n){ static char*(*real)(const char*); if(!real) real=dlsym(RTLD_NEXT,"getenv"); dl_iterate_phdr(cb,0); if(!strcmp(n,"LD_PRELOAD")) return 0; return real(n); }
