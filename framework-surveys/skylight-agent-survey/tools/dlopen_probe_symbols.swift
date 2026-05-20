#!/usr/bin/env swift
import Darwin
import Foundation

let candidates = [
    "/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight",
    "/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/SkyLight",
]

let symbols = [
    "SLSMainConnectionID",
    "CGSMainConnectionID",
    "SLSNewConnection",
    "SLSReleaseConnection",
    "SLSCopyManagedDisplays",
    "SLSCopyManagedDisplaySpaces",
    "SLSCopySpacesForWindows",
    "SLSGetActiveSpace",
    "SLSManagedDisplayGetCurrentSpace",
    "SLSGetWindowBounds",
    "SLSGetWindowOwner",
    "SLSGetWindowLevel",
    "SLSSetWindowLevel",
    "SLSMoveWindow",
    "SLSOrderWindow",
    "SLSSetWindowTags",
    "SLSClearWindowTags",
    "SLSTransactionCreate",
    "SLSTransactionCommit",
    "SLSHWCaptureWindowList",
    "SLPSPostEventRecordTo",
    "_SLPSGetFrontProcess",
    "SLEventPostToPid",
    "SLEventSetAuthenticationMessage",
    "SLSEventAuthenticationMessage",
]

var handle: UnsafeMutableRawPointer?
var loadedPath: String?
for path in candidates {
    if let h = dlopen(path, RTLD_LAZY | RTLD_LOCAL) {
        handle = h
        loadedPath = path
        break
    }
}

guard let handle else {
    fputs("ERROR: failed to dlopen SkyLight candidates\n", stderr)
    exit(1)
}

defer { dlclose(handle) }
print("loaded_path\t\(loadedPath ?? "unknown")")
print("symbol\tstatus")
for symbol in symbols.sorted() {
    let ptr = dlsym(handle, symbol)
    print("\(symbol)\t\(ptr == nil ? "missing" : "present")")
}
