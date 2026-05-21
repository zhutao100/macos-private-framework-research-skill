#include "IntelligenceFlowPresence.h"

#include <stdio.h>

static void print_bool(const char *key, bool value, bool trailing_comma) {
    printf("\"%s\":%s%s", key, value ? "true" : "false", trailing_comma ? "," : "");
}

int main(void) {
    IntelligenceFlowPresenceRecord records[sizeof(IntelligenceFlowFrameworks) / sizeof(IntelligenceFlowFrameworks[0])];
    size_t count = IntelligenceFlowPresenceCheckAll(records, IntelligenceFlowFrameworkCount());
    size_t opened = 0;
    size_t fully_present = 0;

    printf("{\"schema_version\":1,\"framework_count\":%zu,\"records\":[", count);
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
        printf("{\"name\":\"%s\",", record->descriptor->name);
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
