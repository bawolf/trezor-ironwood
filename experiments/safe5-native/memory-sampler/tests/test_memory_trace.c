// Host test of the real pinned collector and the unmodified sampler proposal.
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "py/runtime.h"
#include "py/gc.h"
#include "memory_trace.h"

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x); exit(1); } } while (0)
#define BLOCK MICROPY_BYTES_PER_GC_BLOCK
#define LIMIT 2048

mp_state_ctx_t mp_state_ctx;
static unsigned char first[32768] __attribute__((aligned(32)));
static unsigned char second[16384] __attribute__((aligned(32)));
static unsigned char *starts[2];
static size_t blocks[2];
static unsigned char occupied[2][LIMIT];
static void *roots[LIMIT];
static size_t lengths[LIMIT];
static size_t allocations, frees, reallocations, collections, samples;
static unsigned checks;

// Only symbol names in gc.c are changed at compile time for observation.
// Every wrapper delegates to the actual collector; no gc_info values are faked.
void gc_info_real(gc_info_t *info);
void *gc_alloc_real(size_t size, unsigned flags);
void gc_free_real(void *ptr);
void *gc_realloc_real(void *ptr, size_t size, bool allow_move);
void gc_info(gc_info_t *info) { ++samples; gc_info_real(info); }
void *gc_alloc(size_t size, unsigned flags) { ++allocations; return gc_alloc_real(size, flags); }
void gc_free(void *ptr) { ++frees; gc_free_real(ptr); }
void *gc_realloc(void *ptr, size_t size, bool move) {
    ++reallocations; return gc_realloc_real(ptr, size, move);
}

// Explicit test roots replace the Unix port's register/stack-root discovery.
void gc_collect(void) {
    ++collections;
    gc_collect_start();
    gc_collect_root(roots, LIMIT);
    gc_collect_end();
}

// Finalizer support remains compiled in, but these raw allocations have no
// finalizer flag. Reaching object-runtime callbacks is a test failure.
void mp_load_method_maybe(mp_obj_t base, qstr attr, mp_obj_t *dest) {
    (void)base; (void)attr; (void)dest; CHECK(0);
}
mp_obj_t mp_call_function_1_protected(mp_obj_t fun, mp_obj_t arg) {
    (void)fun; (void)arg; CHECK(0); return MP_OBJ_NULL;
}

static void mark(void *ptr, size_t length, unsigned char value) {
    uintptr_t address = (uintptr_t)ptr;
    for (size_t area = 0; area < 2; ++area) {
        uintptr_t start = (uintptr_t)starts[area];
        if (address >= start && address < start + blocks[area] * BLOCK) {
            CHECK((address - start) % BLOCK == 0);
            size_t index = (address - start) / BLOCK;
            CHECK(index + length <= blocks[area]);
            for (size_t j = index; j < index + length; ++j) {
                CHECK(occupied[area][j] != value);
                occupied[area][j] = value;
            }
            return;
        }
    }
    CHECK(0);
}

static size_t allocate(size_t bytes) {
    void *ptr = gc_alloc(bytes, 0);
    CHECK(ptr != NULL);
    for (size_t slot = 0; slot < LIMIT; ++slot) {
        if (roots[slot] == NULL) {
            roots[slot] = ptr;
            lengths[slot] = (bytes + BLOCK - 1) / BLOCK;
            mark(ptr, lengths[slot], 1);
            return slot;
        }
    }
    CHECK(0); return 0;
}

static void release(size_t slot) {
    CHECK(roots[slot] != NULL);
    mark(roots[slot], lengths[slot], 0);
    gc_free(roots[slot]);
    roots[slot] = NULL;
}

static ironwood_memory_record_t expected(void) {
    ironwood_memory_record_t result = {0};
    // Independent occupancy model: only returned addresses and requested rounded
    // lengths enter it. It never reads the collector allocation table.
    for (size_t area = 0; area < 2; ++area) {
        size_t run = 0;
        for (size_t j = 0; j < blocks[area]; ++j) {
            if (occupied[area][j]) { result.used_bytes += BLOCK; run = 0; }
            else {
                result.free_bytes += BLOCK;
                run += BLOCK;
                if (run > result.largest_free_bytes) result.largest_free_bytes = run;
            }
        }
    }
    return result;
}

static void capture(enum ironwood_memory_phase phase) {
    size_t a = allocations, f = frees, r = reallocations, c = collections, s = samples;
    ironwood_memory_capture(phase);
    CHECK(allocations == a && frees == f && reallocations == r && collections == c);
    CHECK(samples == s + 1);
    ironwood_memory_record_t want = expected();
    const ironwood_memory_trace_t *trace = ironwood_memory_get();
    const ironwood_memory_record_t *got = &trace->records[phase];
    CHECK(got->used_bytes == want.used_bytes);
    CHECK(got->free_bytes == want.free_bytes);
    CHECK(got->largest_free_bytes == want.largest_free_bytes);
    CHECK(trace->valid_phases & (UINT32_C(1) << phase));
    gc_info_t info;
    gc_info(&info);
    CHECK(info.max_free * BLOCK == want.largest_free_bytes);
    CHECK(info.used + info.free == (blocks[0] + blocks[1]) * BLOCK);
}

static void check_reset(void) {
    ironwood_memory_reset();
    const ironwood_memory_trace_t *trace = ironwood_memory_get();
    CHECK(trace->valid_phases == 0);
    for (int phase = 0; phase < IRONWOOD_MEMORY_PHASE_COUNT; ++phase) {
        CHECK(trace->records[phase].used_bytes == 0);
        CHECK(trace->records[phase].free_bytes == 0);
        CHECK(trace->records[phase].largest_free_bytes == 0);
    }
}

static void passed(const char *name) { ++checks; printf("PASS %s\n", name); }

int main(void) {
    CHECK(MICROPY_GC_SPLIT_HEAP == 1 && MICROPY_GC_SPLIT_HEAP_AUTO == 0);
    gc_init(first, first + sizeof(first));
    gc_add(second, second + sizeof(second));
    MP_STATE_MEM(gc_auto_collect_enabled) = 0; // Preserve occupancy on failed requests.
    mp_state_mem_area_t *area = &MP_STATE_MEM(area);
    for (size_t i = 0; i < 2; ++i) {
        CHECK(area != NULL);
        starts[i] = area->gc_pool_start;
        blocks[i] = (area->gc_pool_end - area->gc_pool_start) / BLOCK;
        CHECK(blocks[i] > 0 && blocks[i] < LIMIT);
        area = area->next;
    }
    CHECK(area == NULL);
    const ironwood_memory_trace_t *view = ironwood_memory_get();
    check_reset();
    capture(IRONWOOD_MEMORY_INPUT_READY);
    ironwood_memory_record_t empty = expected();
    printf("LAYOUT pointer=%zu enum=%zu block=%zu area_header=%zu raw=%zu+%zu usable=%zu+%zu\n",
           sizeof(void *), sizeof(enum ironwood_memory_phase), (size_t)BLOCK, sizeof(mp_state_mem_area_t), sizeof(first),
           sizeof(second), blocks[0] * BLOCK, blocks[1] * BLOCK);
    CHECK(empty.used_bytes == 0 && empty.free_bytes > empty.largest_free_bytes);
    passed("empty_pools_trailing_run_and_block_to_byte_conversion");

    // One allocation cannot combine the two areas even with sufficient sum free.
    ironwood_memory_trace_t before = *view;
    CHECK(gc_alloc(empty.largest_free_bytes + BLOCK, 0) == NULL);
    CHECK(memcmp(view, &before, sizeof(before)) == 0);
    capture(IRONWOOD_MEMORY_BEFORE_RESPONSE);
    passed("disjoint_pools_failure_preserves_record");

    check_reset();
    for (int phase = 0; phase < IRONWOOD_MEMORY_PHASE_COUNT; ++phase) {
        allocate(BLOCK + 1); // Exercise requested-size rounding to two blocks.
        capture((enum ironwood_memory_phase)phase);
        CHECK(view->valid_phases == (UINT32_C(1) << (phase + 1)) - 1);
    }
    CHECK(view == ironwood_memory_get() && view->valid_phases == 63);
    passed("six_phase_bits_and_exact_occupancy");

    before = *view;
    allocate(3 * BLOCK);
    capture(IRONWOOD_MEMORY_REVIEW_READY);
    CHECK(view->records[IRONWOOD_MEMORY_REVIEW_READY].used_bytes > before.records[IRONWOOD_MEMORY_REVIEW_READY].used_bytes);
    before.records[IRONWOOD_MEMORY_REVIEW_READY] = view->records[IRONWOOD_MEMORY_REVIEW_READY];
    CHECK(memcmp(view, &before, sizeof(before)) == 0);
    passed("repeated_phase_overwrites_only_that_record");

    int invalid[] = {-1, IRONWOOD_MEMORY_PHASE_COUNT, IRONWOOD_MEMORY_PHASE_COUNT + 1,
                     32, 255, INT_MIN, INT_MAX};
    for (size_t i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i) {
        size_t s = samples;
        ironwood_memory_capture((enum ironwood_memory_phase)invalid[i]);
        CHECK(samples == s && memcmp(view, &before, sizeof(before)) == 0);
    }
    passed("invalid_phases_do_not_sample_or_change_validity");

    // Release all prior allocations, then fill with one-block objects and make
    // alternating holes. Expected runs come from physical addresses, not order.
    for (size_t i = 0; i < LIMIT; ++i) if (roots[i]) release(i);
    size_t total_blocks = blocks[0] + blocks[1];
    CHECK(total_blocks < LIMIT);
    for (size_t i = 0; i < total_blocks; ++i) allocate(BLOCK);
    CHECK(gc_alloc(BLOCK, 0) == NULL);
    for (size_t i = 0; i < total_blocks; i += 2) release(i);
    capture(IRONWOOD_MEMORY_RESPONSE_RESERVED);
    ironwood_memory_record_t fragmented = expected();
    CHECK(fragmented.largest_free_bytes == BLOCK);
    CHECK(fragmented.free_bytes > 2 * BLOCK);
    before = *view;
    CHECK(gc_alloc(2 * BLOCK, 0) == NULL);
    CHECK(memcmp(view, &before, sizeof(before)) == 0);
    printf("FRAGMENTED used=%zu free=%zu largest=%zu rejected_request=%zu\n",
           fragmented.used_bytes, fragmented.free_bytes, fragmented.largest_free_bytes, (size_t)(2 * BLOCK));
    passed("fragmentation_sum_free_does_not_supply_one_run");

    // Exercise real marking with explicit roots, then real collection after
    // dropping them. No finalizer-bearing objects or VM stack scan are involved.
    gc_collect();
    capture(IRONWOOD_MEMORY_SIGN_RETURNED);
    memset(roots, 0, sizeof(roots));
    memset(occupied, 0, sizeof(occupied));
    gc_collect();
    capture(IRONWOOD_MEMORY_CANCELLED);
    CHECK(expected().free_bytes == empty.free_bytes);
    size_t recovered = allocate(BLOCK + 1);
    capture(IRONWOOD_MEMORY_INPUT_READY);
    release(recovered);
    capture(IRONWOOD_MEMORY_CANCELLED);
    passed("real_collection_cleanup_and_recovery");

    size_t a = allocations, f = frees, r = reallocations, c = collections, s = samples;
    check_reset();
    CHECK(view == ironwood_memory_get());
    CHECK(allocations == a && frees == f && reallocations == r && collections == c && samples == s);
    passed("explicit_reset_clears_live_view_without_gc_work");
    printf("RESULT checks=%u collections=%zu samples=%zu\n", checks, collections, samples);
    return checks == 8 ? 0 : 1;
}
