#include "IntelligenceFlowPresence.h"

#include <stdio.h>
#include <sys/sysctl.h>
#include <sys/utsname.h>

static void copy_sysctl_string(const char *name, char *buffer, size_t buffer_size) {
    if (buffer_size == 0) {
        return;
    }
    buffer[0] = '\0';
    size_t size = buffer_size;
    if (sysctlbyname(name, buffer, &size, NULL, 0) != 0 || size == 0) {
        snprintf(buffer, buffer_size, "unknown");
    }
}

static void print_escaped_string(const char *value) {
    if (!value) {
        return;
    }
    for (const unsigned char *cursor = (const unsigned char *)value; *cursor; cursor++) {
        switch (*cursor) {
            case '\\':
                printf("\\\\");
                break;
            case '"':
                printf("\\\"");
                break;
            case '\n':
                printf("\\n");
                break;
            case '\r':
                printf("\\r");
                break;
            case '\t':
                printf("\\t");
                break;
            default:
                if (*cursor < 0x20) {
                    printf("\\u%04x", *cursor);
                } else {
                    putchar(*cursor);
                }
                break;
        }
    }
}

static void print_string(const char *key, const char *value, bool trailing_comma) {
    printf("\"%s\":\"", key);
    print_escaped_string(value ? value : "");
    printf("\"%s", trailing_comma ? "," : "");
}

static void print_nullable_string(const char *key, const char *value, bool trailing_comma) {
    printf("\"%s\":", key);
    if (value) {
        printf("\"");
        print_escaped_string(value);
        printf("\"");
    } else {
        printf("null");
    }
    printf("%s", trailing_comma ? "," : "");
}

static void print_bool(const char *key, bool value, bool trailing_comma) {
    printf("\"%s\":%s%s", key, value ? "true" : "false", trailing_comma ? "," : "");
}

int main(void) {
    IntelligenceFlowPresenceRecord records[sizeof(IntelligenceFlowFrameworks) / sizeof(IntelligenceFlowFrameworks[0])];
    size_t count = IntelligenceFlowPresenceCheckAll(records, IntelligenceFlowFrameworkCount());
    size_t opened = 0;
    size_t fully_present = 0;
    char product_version[64];
    char build_version[64];
    struct utsname uts;

    copy_sysctl_string("kern.osproductversion", product_version, sizeof(product_version));
    copy_sysctl_string("kern.osversion", build_version, sizeof(build_version));
    uname(&uts);

    printf("{\"schema_version\":1,\"build\":{");
    print_string("product_version", product_version, true);
    print_string("build_version", build_version, true);
    print_string("darwin_version", uts.release, true);
    print_string("architecture", uts.machine, false);
    printf("},\"framework_count\":%zu,\"records\":[", count);
    for (size_t index = 0; index < count; index++) {
        IntelligenceFlowPresenceRecord *record = &records[index];
        bool present = record->opened &&
                       record->version_symbol_present &&
                       record->class_present &&
                       record->protocol_present;
        opened += record->opened ? 1 : 0;
        fully_present += present ? 1 : 0;

        if (index > 0) {
            printf(",");
        }
        printf("{");
        print_string("name", record->descriptor->name, true);
        print_string("path", record->descriptor->path, true);
        print_nullable_string("version_symbol", record->descriptor->version_symbol, true);
        print_nullable_string("representative_class", record->descriptor->representative_class, true);
        print_nullable_string("representative_protocol", record->descriptor->representative_protocol, true);
        print_bool("opened", record->opened, true);
        print_bool("version_symbol_present", record->version_symbol_present, true);
        print_bool("class_present", record->class_present, true);
        print_bool("protocol_present", record->protocol_present, true);
        print_bool("fully_present", present, false);
        printf("}");
    }
    printf("],\"summary\":{\"opened\":%zu,\"fully_present\":%zu,\"missing\":%zu}}\n", opened, fully_present, count - fully_present);

    IntelligenceFlowPresenceCloseAll(records, count);
    return fully_present == count ? 0 : 1;
}
