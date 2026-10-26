#include "chunk_capacity.h"
#include <stdio.h>
#include <string.h>

int main(void) {
    size_t capacity = 16, used = 16;
    unsigned char *buffer = (unsigned char*)malloc(capacity);
    if (!buffer) return 1;
    memset(buffer, 0x5A, capacity);
    if (!ensure_chunk_capacity(&buffer, &capacity, used, 60)) return 2;
    if (capacity != 76) return 3;
    for (size_t i = 0; i < 16; ++i) if (buffer[i] != 0x5A) return 4;
    memset(buffer + used, 0xC3, 60);
    used += 60;
    for (size_t i = 0; i < 12; ++i) {
        const size_t appended = 16384 + i;
        if (!ensure_chunk_capacity(&buffer, &capacity, used, appended)) return 5;
        memset(buffer + used, (int)i, appended);
        used += appended;
        if (capacity != used) return 6;
    }
    unsigned char *prior = buffer;
    if (ensure_chunk_capacity(&buffer, &capacity, SIZE_MAX - 2, 16)) return 7;
    if (capacity != used || buffer != prior) return 8;
    for (size_t i = 0; i < 16; ++i) if (buffer[i] != 0x5A) return 9;
    if (!ensure_chunk_capacity(&buffer, &capacity, 0, 1)) return 10;
    if (capacity != used) return 11;
    free(buffer);
    puts("PASS: dynamic chunk capacity, data retention, overflow rejection, no-op");
    return 0;
}
