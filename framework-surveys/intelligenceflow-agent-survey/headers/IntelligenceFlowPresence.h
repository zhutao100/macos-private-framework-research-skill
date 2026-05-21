/*
  IntelligenceFlow presence declaration set for dlsym/Objective-C runtime probes.

  Scope:
  - open the nine IntelligenceFlow framework-family images through dyld;
  - verify version symbols;
  - verify representative Objective-C class/protocol registration where available.

  Verification baseline:
  - macOS 15.7.2 build 24G325;
  - framework family version 218.5.0;
  - compiled with the macOS 26.2 SDK;
  - macOS 26.2 build 25C56;
  - framework family version 3505.5.1;
  - compiled with the macOS 26.4 SDK;
  - validated by scripts/verify_intelligenceflow_presence_header.zsh.

  This header intentionally does not declare callable private framework APIs.
*/
#pragma once

#include <dlfcn.h>
#include <objc/runtime.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct IntelligenceFlowFrameworkDescriptor {
    const char *name;
    const char *path;
    const char *version_symbol;
    const char *representative_class;
    const char *representative_protocol;
} IntelligenceFlowFrameworkDescriptor;

typedef struct IntelligenceFlowPresenceRecord {
    const IntelligenceFlowFrameworkDescriptor *descriptor;
    void *handle;
    bool opened;
    bool version_symbol_present;
    bool class_present;
    bool protocol_present;
} IntelligenceFlowPresenceRecord;

static const IntelligenceFlowFrameworkDescriptor IntelligenceFlowFrameworks[] = {
    {
        "IntelligenceFlow",
        "/System/Library/PrivateFrameworks/IntelligenceFlow.framework/IntelligenceFlow",
        "IntelligenceFlowVersionNumber",
        "_TtC16IntelligenceFlow9Readiness",
        "LXToolboxXPCProtocol",
    },
    {
        "IntelligenceFlowAppIntentsPreviewToolSupport",
        "/System/Library/PrivateFrameworks/IntelligenceFlowAppIntentsPreviewToolSupport.framework/IntelligenceFlowAppIntentsPreviewToolSupport",
        "IntelligenceFlowAppIntentsPreviewToolSupportVersionNumber",
        NULL,
        NULL,
    },
    {
        "IntelligenceFlowContext",
        "/System/Library/PrivateFrameworks/IntelligenceFlowContext.framework/IntelligenceFlowContext",
        "IntelligenceFlowContextVersionNumber",
        "_TtC23IntelligenceFlowContext13ContextClient",
        "LXUIContextXPCProtocol",
    },
    {
        "IntelligenceFlowContextRuntime",
        "/System/Library/PrivateFrameworks/IntelligenceFlowContextRuntime.framework/IntelligenceFlowContextRuntime",
        "IntelligenceFlowContextRuntimeVersionNumber",
        "_TtC30IntelligenceFlowContextRuntime16ContextRetriever",
        "LXContextXPCProtocol",
    },
    {
        "IntelligenceFlowFeedbackDataCollector",
        "/System/Library/PrivateFrameworks/IntelligenceFlowFeedbackDataCollector.framework/IntelligenceFlowFeedbackDataCollector",
        "IntelligenceFlowFeedbackDataCollectorVersionNumber",
        "_TtC37IntelligenceFlowFeedbackDataCollector20DeviceContextBuilder",
        NULL,
    },
    {
        "IntelligenceFlowPlannerRuntime",
        "/System/Library/PrivateFrameworks/IntelligenceFlowPlannerRuntime.framework/IntelligenceFlowPlannerRuntime",
        "IntelligenceFlowPlannerRuntimeVersionNumber",
        "_TtC30IntelligenceFlowPlannerRuntime18FullPlannerService",
        NULL,
    },
    {
        "IntelligenceFlowPlannerSupport",
        "/System/Library/PrivateFrameworks/IntelligenceFlowPlannerSupport.framework/IntelligenceFlowPlannerSupport",
        "IntelligenceFlowPlannerSupportVersionNumber",
        "_TtC30IntelligenceFlowPlannerSupport16QueryableToolbox",
        NULL,
    },
    {
        "IntelligenceFlowRuntime",
        "/System/Library/PrivateFrameworks/IntelligenceFlowRuntime.framework/IntelligenceFlowRuntime",
        "IntelligenceFlowRuntimeVersionNumber",
        "_TtC23IntelligenceFlowRuntime8Executor",
        "LXSessionXPCServerProtocol",
    },
    {
        "IntelligenceFlowShared",
        "/System/Library/PrivateFrameworks/IntelligenceFlowShared.framework/IntelligenceFlowShared",
        "IntelligenceFlowSharedVersionNumber",
        "_TtC22IntelligenceFlowShared20QueryDecorationInput",
        "LXContextXPCProtocol",
    },
};

static inline size_t IntelligenceFlowFrameworkCount(void) {
    return sizeof(IntelligenceFlowFrameworks) / sizeof(IntelligenceFlowFrameworks[0]);
}

static inline void IntelligenceFlowPresenceInit(IntelligenceFlowPresenceRecord *record) {
    if (record) {
        memset(record, 0, sizeof(*record));
    }
}

static inline bool IntelligenceFlowPresenceOpen(
    const IntelligenceFlowFrameworkDescriptor *descriptor,
    IntelligenceFlowPresenceRecord *record
) {
    if (!descriptor || !record) {
        return false;
    }

    IntelligenceFlowPresenceInit(record);
    record->descriptor = descriptor;
    record->handle = dlopen(descriptor->path, RTLD_LAZY | RTLD_LOCAL);
    record->opened = record->handle != NULL;
    if (!record->opened) {
        return false;
    }

    record->version_symbol_present =
        descriptor->version_symbol == NULL || dlsym(record->handle, descriptor->version_symbol) != NULL;
    record->class_present =
        descriptor->representative_class == NULL || objc_getClass(descriptor->representative_class) != Nil;
    record->protocol_present =
        descriptor->representative_protocol == NULL || objc_getProtocol(descriptor->representative_protocol) != NULL;

    return record->version_symbol_present && record->class_present && record->protocol_present;
}

static inline size_t IntelligenceFlowPresenceCheckAll(
    IntelligenceFlowPresenceRecord *records,
    size_t capacity
) {
    size_t count = IntelligenceFlowFrameworkCount();
    if (!records || capacity < count) {
        return 0;
    }
    for (size_t index = 0; index < count; index++) {
        (void)IntelligenceFlowPresenceOpen(&IntelligenceFlowFrameworks[index], &records[index]);
    }
    return count;
}

static inline void IntelligenceFlowPresenceClose(IntelligenceFlowPresenceRecord *record) {
    if (record && record->handle) {
        dlclose(record->handle);
        record->handle = NULL;
    }
}

static inline void IntelligenceFlowPresenceCloseAll(
    IntelligenceFlowPresenceRecord *records,
    size_t count
) {
    if (!records) {
        return;
    }
    for (size_t index = 0; index < count; index++) {
        IntelligenceFlowPresenceClose(&records[index]);
    }
}

#ifdef __cplusplus
}
#endif
