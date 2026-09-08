/* TEST ONLY. C starts before Rust alloc and owns all file I/O and export. */
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define INPUT_CAPACITY 65537
#define OUTPUT_CAPACITY 65536

enum mode { SIGN, CANCEL, REPLACE, OOM_BEGIN, OOM_SIGN };
enum status { OK, REJECTED, OUTPUT_TOO_SMALL };
enum driver_exit { USAGE = 64, INPUT_ERROR, WRONG_STATUS, STAGING_CHANGED,
                   OUTPUT_ERROR, OPEN_ERROR, WRITE_ERROR, STDERR_ERROR };
enum fault { PREINIT = 1, DOUBLE_INIT, REENTRY, PANIC, SEALED_FREE, LATE_OWNER };

struct counts {
    size_t attempts, allocations, deallocations, failures, requested_total;
    size_t rounded_total, live_requested, live_blocks, peak_requested, peak_used;
    size_t largest_request, used, free;
};
struct layout_facts { size_t size, alignment, rounded; };
struct init_report {
    struct counts before, after;
    struct layout_facts layouts[5];
};
struct report {
    struct counts baseline, start, phases[6], recovery;
    size_t phase_mask, serialized_bytes, signatures, recovered_large_block;
};
extern void arena_probe_init(void);
extern void arena_probe_public_init(struct init_report *);
extern int rust_eh_personality(int, int, uint64_t, void *, void *);
extern void arena_probe_layout_tests(void);
extern void arena_probe_fault(uint32_t mode);
extern int32_t arena_probe_run(const uint8_t *, size_t, uint8_t *, size_t,
                               struct report *, uint32_t);

static uint8_t input[INPUT_CAPACITY], output[OUTPUT_CAPACITY];
static struct report report;
static struct init_report startup, repeated_init;

static void print_counts(const struct counts *c) {
    printf("{\"attempts\":%zu,\"allocations\":%zu,\"deallocations\":%zu,\"failures\":%zu,"
           "\"requested_total\":%zu,\"rounded_total\":%zu,\"live_requested\":%zu,\"live_blocks\":%zu,"
           "\"peak_requested\":%zu,\"peak_used\":%zu,\"largest_request\":%zu,\"used\":%zu,\"free\":%zu}",
           c->attempts, c->allocations, c->deallocations, c->failures, c->requested_total,
           c->rounded_total, c->live_requested, c->live_blocks, c->peak_requested,
           c->peak_used, c->largest_request, c->used, c->free);
}

static void print_report(int status) {
    static const char *names[] = {"constructor", "begin", "approve", "sign", "serialize", "teardown"};
    printf("{\"schema_version\":2,\"status\":%d,\"phase_mask\":%zu,\"serialized_bytes\":%zu,"
           "\"signatures\":%zu,\"recovered_large_block\":%zu,\"startup\":{\"cold\":",
           status, report.phase_mask, report.serialized_bytes, report.signatures, report.recovered_large_block);
    print_counts(&startup.before);
    printf(",\"ready\":"); print_counts(&startup.after);
    printf(",\"repeat_before\":"); print_counts(&repeated_init.before);
    printf(",\"repeat_after\":"); print_counts(&repeated_init.after);
    printf(",\"layouts\":[");
    for (size_t i = 0; i < 5; ++i) {
        const struct layout_facts *l = &startup.layouts[i];
        printf("%s{\"size\":%zu,\"alignment\":%zu,\"rounded\":%zu}",
               i ? "," : "", l->size, l->alignment, l->rounded);
    }
    printf("]},\"baseline\":"); print_counts(&report.baseline);
    printf(",\"start\":"); print_counts(&report.start);
    printf(",\"phases\":{");
    for (size_t i = 0; i < 6; ++i) {
        printf("%s\"%s\":", i ? "," : "", names[i]); print_counts(&report.phases[i]);
    }
    printf("},\"recovery\":"); print_counts(&report.recovery);
    puts("}");
}

static int run_one(const char *source, const char *destination, enum mode mode,
                   size_t output_capacity, enum status expected_status) {
    FILE *file = fopen(source, "rb");
    if (!file) return INPUT_ERROR;
    size_t size = fread(input, 1, sizeof(input), file);
    int failed = ferror(file) || fgetc(file) != EOF;
    if (fclose(file)) failed = 1;
    if (failed) return INPUT_ERROR;
    memset(output, 0xc7, sizeof(output));
    memset(&report, 0, sizeof(report));
    int result = arena_probe_run(input, size, output, output_capacity, &report, (uint32_t)mode);
    print_report(result);
    if (fflush(stdout) == EOF) return WRITE_ERROR;
    if (result != (int)expected_status) return WRONG_STATUS;
    if (result || mode != SIGN) {
        for (size_t i = 0; i < sizeof(output); ++i) if (output[i] != 0xc7) return STAGING_CHANGED;
        return 0;
    }
    /* Every request owner dropped and both recovery gates passed before export. */
    if (!report.serialized_bytes || report.serialized_bytes > sizeof(output)) return OUTPUT_ERROR;
    file = fopen(destination, "wbx");
    if (!file) return OPEN_ERROR;
    failed = fwrite(output, 1, report.serialized_bytes, file) != report.serialized_bytes;
    if (fclose(file)) failed = 1;
    return failed ? WRITE_ERROR : 0;
}

int main(int argc, char **argv) {
    /* If stderr is inherited, O_NONBLOCK affects every process sharing it. */
    int flags = fcntl(STDERR_FILENO, F_GETFL);
    if (flags == -1 || fcntl(STDERR_FILENO, F_SETFL, flags | O_NONBLOCK) == -1) return STDERR_ERROR;
    if (argc == 2 && strcmp(argv[1], "preinit") == 0) arena_probe_fault(PREINIT);
    arena_probe_init();
    if (argc == 2) {
        if (strcmp(argv[1], "double-init") == 0) arena_probe_fault(DOUBLE_INIT);
        if (strcmp(argv[1], "reentry") == 0) arena_probe_fault(REENTRY);
        if (strcmp(argv[1], "personality") == 0) rust_eh_personality(1, 0, 0, NULL, NULL);
        if (strcmp(argv[1], "panic") == 0) arena_probe_fault(PANIC);
        if (strcmp(argv[1], "layouts") == 0) {
            arena_probe_layout_tests();
            puts("{\"valid_layout_tests\":\"passed\"}");
            return 0;
        }
    }
    /* Before file reads, keys or requests; call the same public initializer twice. */
    arena_probe_public_init(&startup);
    arena_probe_public_init(&repeated_init);
    if (argc == 2 && strcmp(argv[1], "sealed-free") == 0) arena_probe_fault(SEALED_FREE);
    if (argc == 2 && strcmp(argv[1], "late-owner") == 0) arena_probe_fault(LATE_OWNER);
    if (argc == 6 && strcmp(argv[1], "repeat") == 0) {
        for (int i = 2; i < 5; ++i) {
            const char *base = strrchr(argv[i], '/');
            base = base ? base + 1 : argv[i];
            char destination[4096];
            int count = snprintf(destination, sizeof(destination), "%s/%s", argv[5], base);
            if (count < 0 || (size_t)count >= sizeof(destination)) return OUTPUT_ERROR;
            int result = run_one(argv[i], destination, SIGN, sizeof(output), OK);
            if (result) return result;
        }
        return 0;
    }
    if (argc != 4) return USAGE;
    enum mode mode = SIGN;
    enum status expected = OK;
    size_t capacity = sizeof(output);
    if (strcmp(argv[1], "cancel") == 0) mode = CANCEL;
    else if (strcmp(argv[1], "replace") == 0) mode = REPLACE;
    else if (strcmp(argv[1], "oom-begin") == 0) mode = OOM_BEGIN;
    else if (strcmp(argv[1], "oom-sign") == 0) mode = OOM_SIGN;
    else if (strcmp(argv[1], "small-output") == 0) { capacity = 1; expected = OUTPUT_TOO_SMALL; }
    else if (strcmp(argv[1], "reject") == 0) expected = REJECTED;
    else if (strcmp(argv[1], "sign") != 0) return USAGE;
    return run_one(argv[2], argv[3], mode, capacity, expected);
}
