/*
  SkyLight read-only declaration set for dlsym-based project probes.

  Scope:
  - connection identity;
  - managed display/Space observation;
  - read-only window geometry/owner/level observation.

  Verification baseline:
  - resolved through a SkyLight.framework dlopen handle on macOS 15.7.2 build 24G325;
  - prototype-compatible with non-mutating calls in
    tools/verify_skylight_readonly_header.zsh on macOS 15.7.2 build 24G325;
  - the same non-mutating calls passed on macOS 26.2 build 25C56;
  - clang syntax validation passed on macOS SDK 26.4;
  - cross-checked against yabai `extern.h` and Hammerspoon `hs.spaces`
    declarations as caller evidence.

  Use these declarations through dlsym. Avoid hard-linking to SkyLight.
  Call SkyLightReadOnlyInit or zero-initialize SkyLightReadOnlySymbols before
  SkyLightReadOnlyLoad.
*/
#pragma once

#include <CoreFoundation/CoreFoundation.h>
#include <CoreGraphics/CoreGraphics.h>
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef int32_t SLSConnectionID;
typedef uint32_t SLSWindowID;
typedef uint64_t SLSSpaceID;
typedef CGError SLSStatus;

typedef SLSConnectionID (*SLSMainConnectionIDFunction)(void);
typedef SLSConnectionID (*CGSMainConnectionIDFunction)(void);

typedef CFArrayRef (*SLSCopyManagedDisplaysFunction)(SLSConnectionID cid);
typedef CFArrayRef (*SLSCopyManagedDisplaySpacesFunction)(SLSConnectionID cid);
typedef CFArrayRef (*SLSCopySpacesForWindowsFunction)(
    SLSConnectionID cid,
    int32_t selector,
    CFArrayRef window_list
);
typedef CFArrayRef (*SLSCopyWindowsWithOptionsAndTagsFunction)(
    SLSConnectionID cid,
    uint32_t owner,
    CFArrayRef spaces,
    uint32_t options,
    uint64_t *set_tags,
    uint64_t *clear_tags
);
typedef SLSSpaceID (*SLSGetActiveSpaceFunction)(SLSConnectionID cid);
typedef SLSSpaceID (*SLSManagedDisplayGetCurrentSpaceFunction)(
    SLSConnectionID cid,
    CFStringRef uuid
);
typedef int32_t (*SLSSpaceGetTypeFunction)(SLSConnectionID cid, SLSSpaceID sid);

typedef SLSStatus (*SLSGetWindowBoundsFunction)(
    SLSConnectionID cid,
    SLSWindowID wid,
    CGRect *frame
);
typedef SLSStatus (*SLSGetWindowOwnerFunction)(
    SLSConnectionID cid,
    SLSWindowID wid,
    SLSConnectionID *owner_cid
);
typedef SLSStatus (*SLSGetWindowLevelFunction)(
    SLSConnectionID cid,
    SLSWindowID wid,
    int32_t *level
);

typedef struct SkyLightReadOnlySymbols {
    void *handle;
    const char *loaded_path;
    SLSMainConnectionIDFunction SLSMainConnectionID;
    CGSMainConnectionIDFunction CGSMainConnectionID;
    SLSCopyManagedDisplaysFunction SLSCopyManagedDisplays;
    SLSCopyManagedDisplaySpacesFunction SLSCopyManagedDisplaySpaces;
    SLSCopySpacesForWindowsFunction SLSCopySpacesForWindows;
    SLSCopyWindowsWithOptionsAndTagsFunction SLSCopyWindowsWithOptionsAndTags;
    SLSGetActiveSpaceFunction SLSGetActiveSpace;
    SLSManagedDisplayGetCurrentSpaceFunction SLSManagedDisplayGetCurrentSpace;
    SLSSpaceGetTypeFunction SLSSpaceGetType;
    SLSGetWindowBoundsFunction SLSGetWindowBounds;
    SLSGetWindowOwnerFunction SLSGetWindowOwner;
    SLSGetWindowLevelFunction SLSGetWindowLevel;
} SkyLightReadOnlySymbols;

static inline void SkyLightReadOnlyInit(SkyLightReadOnlySymbols *symbols) {
    if (symbols) {
        memset(symbols, 0, sizeof(*symbols));
    }
}

static inline bool SkyLightReadOnlyOpen(SkyLightReadOnlySymbols *symbols) {
    if (!symbols) {
        return false;
    }

    const char *paths[] = {
        "/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight",
        "/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/SkyLight",
        NULL,
    };

    for (const char **path = paths; *path; path++) {
        void *handle = dlopen(*path, RTLD_LAZY | RTLD_LOCAL);
        if (handle) {
            symbols->handle = handle;
            symbols->loaded_path = *path;
            return true;
        }
    }
    return false;
}

static inline bool SkyLightReadOnlyLoad(SkyLightReadOnlySymbols *symbols) {
    if (!symbols) {
        return false;
    }
    if (!symbols->handle && !SkyLightReadOnlyOpen(symbols)) {
        return false;
    }

    symbols->SLSMainConnectionID =
        (SLSMainConnectionIDFunction)dlsym(symbols->handle, "SLSMainConnectionID");
    symbols->CGSMainConnectionID =
        (CGSMainConnectionIDFunction)dlsym(symbols->handle, "CGSMainConnectionID");
    symbols->SLSCopyManagedDisplays =
        (SLSCopyManagedDisplaysFunction)dlsym(symbols->handle, "SLSCopyManagedDisplays");
    symbols->SLSCopyManagedDisplaySpaces =
        (SLSCopyManagedDisplaySpacesFunction)dlsym(symbols->handle, "SLSCopyManagedDisplaySpaces");
    symbols->SLSCopySpacesForWindows =
        (SLSCopySpacesForWindowsFunction)dlsym(symbols->handle, "SLSCopySpacesForWindows");
    symbols->SLSCopyWindowsWithOptionsAndTags =
        (SLSCopyWindowsWithOptionsAndTagsFunction)dlsym(
            symbols->handle,
            "SLSCopyWindowsWithOptionsAndTags"
        );
    symbols->SLSGetActiveSpace =
        (SLSGetActiveSpaceFunction)dlsym(symbols->handle, "SLSGetActiveSpace");
    symbols->SLSManagedDisplayGetCurrentSpace =
        (SLSManagedDisplayGetCurrentSpaceFunction)dlsym(
            symbols->handle,
            "SLSManagedDisplayGetCurrentSpace"
        );
    symbols->SLSSpaceGetType =
        (SLSSpaceGetTypeFunction)dlsym(symbols->handle, "SLSSpaceGetType");
    symbols->SLSGetWindowBounds =
        (SLSGetWindowBoundsFunction)dlsym(symbols->handle, "SLSGetWindowBounds");
    symbols->SLSGetWindowOwner =
        (SLSGetWindowOwnerFunction)dlsym(symbols->handle, "SLSGetWindowOwner");
    symbols->SLSGetWindowLevel =
        (SLSGetWindowLevelFunction)dlsym(symbols->handle, "SLSGetWindowLevel");

    return symbols->SLSMainConnectionID &&
           symbols->SLSCopyManagedDisplays &&
           symbols->SLSCopyManagedDisplaySpaces &&
           symbols->SLSCopySpacesForWindows &&
           symbols->SLSCopyWindowsWithOptionsAndTags &&
           symbols->SLSGetActiveSpace &&
           symbols->SLSManagedDisplayGetCurrentSpace &&
           symbols->SLSSpaceGetType &&
           symbols->SLSGetWindowBounds &&
           symbols->SLSGetWindowOwner &&
           symbols->SLSGetWindowLevel;
}

static inline void SkyLightReadOnlyClose(SkyLightReadOnlySymbols *symbols) {
    if (symbols && symbols->handle) {
        dlclose(symbols->handle);
        symbols->handle = NULL;
        symbols->loaded_path = NULL;
    }
}

#ifdef SKYLIGHT_ENABLE_DIRECT_PRIVATE_DECLARATIONS
extern SLSConnectionID SLSMainConnectionID(void);
/* Optional compatibility alias; use SLSMainConnectionID as the required symbol. */
extern SLSConnectionID CGSMainConnectionID(void);
extern CFArrayRef SLSCopyManagedDisplays(SLSConnectionID cid);
extern CFArrayRef SLSCopyManagedDisplaySpaces(SLSConnectionID cid);
extern CFArrayRef SLSCopySpacesForWindows(
    SLSConnectionID cid,
    int32_t selector,
    CFArrayRef window_list
);
extern CFArrayRef SLSCopyWindowsWithOptionsAndTags(
    SLSConnectionID cid,
    uint32_t owner,
    CFArrayRef spaces,
    uint32_t options,
    uint64_t *set_tags,
    uint64_t *clear_tags
);
extern SLSSpaceID SLSGetActiveSpace(SLSConnectionID cid);
extern SLSSpaceID SLSManagedDisplayGetCurrentSpace(SLSConnectionID cid, CFStringRef uuid);
extern int32_t SLSSpaceGetType(SLSConnectionID cid, SLSSpaceID sid);
extern SLSStatus SLSGetWindowBounds(SLSConnectionID cid, SLSWindowID wid, CGRect *frame);
extern SLSStatus SLSGetWindowOwner(SLSConnectionID cid, SLSWindowID wid, SLSConnectionID *owner_cid);
extern SLSStatus SLSGetWindowLevel(SLSConnectionID cid, SLSWindowID wid, int32_t *level);
#endif

#ifdef __cplusplus
}
#endif
