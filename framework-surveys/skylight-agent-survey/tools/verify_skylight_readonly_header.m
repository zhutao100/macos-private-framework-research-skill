#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <sys/sysctl.h>

#import "SkyLightReadOnly.h"

static NSString *SystemBuildVersion(void) {
    size_t size = 0;
    if (sysctlbyname("kern.osversion", NULL, &size, NULL, 0) != 0 || size == 0) {
        return @"unknown";
    }
    NSMutableData *data = [NSMutableData dataWithLength:size];
    if (sysctlbyname("kern.osversion", data.mutableBytes, &size, NULL, 0) != 0) {
        return @"unknown";
    }
    const char *bytes = (const char *)data.bytes;
    return [NSString stringWithUTF8String:bytes] ?: @"unknown";
}

static void AddRecord(
    NSMutableArray<NSDictionary *> *records,
    NSString *name,
    NSString *status,
    NSDictionary *details
) {
    NSMutableDictionary *record = [@{
        @"name": name,
        @"status": status,
    } mutableCopy];
    if (details) {
        [record addEntriesFromDictionary:details];
    }
    [records addObject:record];
}

static NSNumber *FirstWindowID(void) {
    CFArrayRef windowInfo = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    );
    NSArray *windows = CFBridgingRelease(windowInfo);
    for (NSDictionary *window in windows) {
        NSNumber *windowNumber = window[(NSString *)kCGWindowNumber];
        if (windowNumber.unsignedIntValue > 0) {
            return windowNumber;
        }
    }
    return nil;
}

int main(void) {
    @autoreleasepool {
        NSMutableArray<NSDictionary *> *records = [NSMutableArray array];
        NSMutableDictionary *report = [NSMutableDictionary dictionary];
        NSOperatingSystemVersion version = NSProcessInfo.processInfo.operatingSystemVersion;
        report[@"product_version"] = [NSString stringWithFormat:@"%ld.%ld.%ld",
                                      (long)version.majorVersion,
                                      (long)version.minorVersion,
                                      (long)version.patchVersion];
        report[@"build_version"] = SystemBuildVersion();

        SkyLightReadOnlySymbols symbols = {0};
        bool loaded = SkyLightReadOnlyLoad(&symbols);
        report[@"loaded_path"] = symbols.loaded_path ? @(symbols.loaded_path) : @"";
        report[@"header_loaded"] = @(loaded);
        if (!loaded) {
            AddRecord(records, @"SkyLightReadOnlyLoad", @"failed", nil);
            report[@"records"] = records;
            NSData *data = [NSJSONSerialization dataWithJSONObject:report
                                                           options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys
                                                             error:nil];
            [data writeToFile:@"/dev/stdout" atomically:NO];
            fputs("\n", stdout);
            SkyLightReadOnlyClose(&symbols);
            return 1;
        }

        SLSConnectionID cid = symbols.SLSMainConnectionID();
        AddRecord(records, @"SLSMainConnectionID", @"called", @{@"connection_id": @(cid)});

        SLSConnectionID cgsCid = symbols.CGSMainConnectionID();
        AddRecord(records, @"CGSMainConnectionID", @"called", @{@"connection_id": @(cgsCid)});

        CFArrayRef displays = symbols.SLSCopyManagedDisplays(cid);
        CFIndex displayCount = displays ? CFArrayGetCount(displays) : -1;
        AddRecord(records,
                  @"SLSCopyManagedDisplays",
                  displays ? @"called" : @"null",
                  @{@"count": @(displayCount)});

        CFArrayRef displaySpaces = symbols.SLSCopyManagedDisplaySpaces(cid);
        AddRecord(records,
                  @"SLSCopyManagedDisplaySpaces",
                  displaySpaces ? @"called" : @"null",
                  @{@"count": @(displaySpaces ? CFArrayGetCount(displaySpaces) : -1)});

        SLSSpaceID activeSpace = symbols.SLSGetActiveSpace(cid);
        AddRecord(records, @"SLSGetActiveSpace", @"called", @{@"space_id": @(activeSpace)});

        int32_t activeSpaceType = symbols.SLSSpaceGetType(cid, activeSpace);
        AddRecord(records, @"SLSSpaceGetType", @"called", @{@"space_type": @(activeSpaceType)});

        if (displays && CFArrayGetCount(displays) > 0) {
            CFTypeRef firstDisplay = CFArrayGetValueAtIndex(displays, 0);
            if (CFGetTypeID(firstDisplay) == CFStringGetTypeID()) {
                SLSSpaceID currentSpace = symbols.SLSManagedDisplayGetCurrentSpace(
                    cid,
                    (CFStringRef)firstDisplay
                );
                AddRecord(records,
                          @"SLSManagedDisplayGetCurrentSpace",
                          @"called",
                          @{@"space_id": @(currentSpace),
                            @"display_type": @"CFString"});
            } else {
                AddRecord(records,
                          @"SLSManagedDisplayGetCurrentSpace",
                          @"skipped",
                          @{@"reason": @"first managed display is not a CFString"});
            }
        } else {
            AddRecord(records,
                      @"SLSManagedDisplayGetCurrentSpace",
                      @"skipped",
                      @{@"reason": @"no managed displays"});
        }

        NSNumber *windowIDForProbes = nil;
        CFNumberRef activeSpaceNumber = CFNumberCreate(NULL, kCFNumberSInt64Type, &activeSpace);
        const void *spaceValues[] = {activeSpaceNumber};
        CFArrayRef activeSpaceArray = CFArrayCreate(NULL, spaceValues, 1, &kCFTypeArrayCallBacks);
        uint64_t setTags = 0;
        uint64_t clearTags = 0;
        CFArrayRef windowsForActiveSpace = symbols.SLSCopyWindowsWithOptionsAndTags(
            cid,
            0,
            activeSpaceArray,
            0x7,
            &setTags,
            &clearTags
        );
        AddRecord(records,
                  @"SLSCopyWindowsWithOptionsAndTags",
                  windowsForActiveSpace ? @"called" : @"null",
                  @{@"count": @(windowsForActiveSpace ? CFArrayGetCount(windowsForActiveSpace) : -1),
                    @"set_tags": @(setTags),
                    @"clear_tags": @(clearTags)});
        if (windowsForActiveSpace) {
            if (CFArrayGetCount(windowsForActiveSpace) > 0) {
                CFTypeRef firstWindow = CFArrayGetValueAtIndex(windowsForActiveSpace, 0);
                if (CFGetTypeID(firstWindow) == CFNumberGetTypeID()) {
                    windowIDForProbes = [(__bridge NSNumber *)firstWindow copy];
                }
            }
            CFRelease(windowsForActiveSpace);
        }
        CFRelease(activeSpaceArray);
        CFRelease(activeSpaceNumber);

        if (windowIDForProbes) {
            const void *windowValues[] = {(__bridge const void *)windowIDForProbes};
            CFArrayRef windowArray = CFArrayCreate(NULL, windowValues, 1, &kCFTypeArrayCallBacks);
            CFArrayRef spacesForWindows = symbols.SLSCopySpacesForWindows(cid, 0x7, windowArray);
            AddRecord(records,
                      @"SLSCopySpacesForWindows",
                      spacesForWindows ? @"called" : @"null",
                      @{@"count": @(spacesForWindows ? CFArrayGetCount(spacesForWindows) : -1),
                        @"window_id": windowIDForProbes});
            if (spacesForWindows) {
                CFRelease(spacesForWindows);
            }
            CFRelease(windowArray);
        } else {
            AddRecord(records,
                      @"SLSCopySpacesForWindows",
                      @"skipped",
                      @{@"reason": @"no window ID from SLSCopyWindowsWithOptionsAndTags"});
        }

        NSNumber *windowID = windowIDForProbes ?: FirstWindowID();
        if (windowID) {
            CGRect bounds = CGRectZero;
            SLSStatus boundsStatus = symbols.SLSGetWindowBounds(
                cid,
                windowID.unsignedIntValue,
                &bounds
            );
            AddRecord(records,
                      @"SLSGetWindowBounds",
                      @"called",
                      @{@"status_code": @(boundsStatus),
                        @"window_id": windowID,
                        @"x": @(bounds.origin.x),
                        @"y": @(bounds.origin.y),
                        @"width": @(bounds.size.width),
                        @"height": @(bounds.size.height)});

            SLSConnectionID owner = 0;
            SLSStatus ownerStatus = symbols.SLSGetWindowOwner(
                cid,
                windowID.unsignedIntValue,
                &owner
            );
            AddRecord(records,
                      @"SLSGetWindowOwner",
                      @"called",
                      @{@"status_code": @(ownerStatus),
                        @"window_id": windowID,
                        @"owner_connection_id": @(owner)});

            int32_t level = 0;
            SLSStatus levelStatus = symbols.SLSGetWindowLevel(
                cid,
                windowID.unsignedIntValue,
                &level
            );
            AddRecord(records,
                      @"SLSGetWindowLevel",
                      @"called",
                      @{@"status_code": @(levelStatus),
                        @"window_id": windowID,
                        @"level": @(level)});
        } else {
            AddRecord(records,
                      @"window_read_probes",
                      @"skipped",
                      @{@"reason": @"CGWindowListCopyWindowInfo returned no on-screen window IDs"});
        }

        if (displaySpaces) {
            CFRelease(displaySpaces);
        }
        if (displays) {
            CFRelease(displays);
        }
        SkyLightReadOnlyClose(&symbols);

        report[@"records"] = records;
        NSData *data = [NSJSONSerialization dataWithJSONObject:report
                                                       options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys
                                                         error:nil];
        [data writeToFile:@"/dev/stdout" atomically:NO];
        fputs("\n", stdout);
    }
    return 0;
}
