/* Test-only GNU linker wrapper: force every realloc to relocate and poison the
 * old storage. Never linked into the shipped executable. */
#include <malloc.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

void *__wrap_realloc(void *old, size_t size) {
    if (!old) return malloc(size);
    if (!size) { free(old); return NULL; }
    size_t old_size = _msize(old);
    void *next = malloc(size);
    if (!next) return NULL;
    memcpy(next, old, old_size < size ? old_size : size);
    memset(old, 0xA5, old_size);
    /* Quarantine until process exit so reads from the old allocation always
       observe the poison, independently of the heap allocator's freelist. */
    fputs("TEST: realloc moved and old bytes poisoned\n", stderr);
    return next;
}
