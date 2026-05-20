#!/usr/bin/env swift
import Darwin
import Foundation

struct ProbeRecord: Encodable {
    let kind: String
    let name: String
    let status: String
}

struct ProbeSummary: Encodable {
    let present: Int
    let missing: Int
    let byKind: [String: [String: Int]]
}

struct BuildInfo: Encodable {
    let productVersion: String
    let buildVersion: String
    let darwinVersion: String
    let architecture: String
}

struct ProbeReport: Encodable {
    let schemaVersion: Int
    let build: BuildInfo
    let loadedPath: String
    let summary: ProbeSummary
    let records: [ProbeRecord]
}

let jsonOutput = CommandLine.arguments.contains("--json")

func sysctlString(_ name: String) -> String {
    var size: size_t = 0
    if sysctlbyname(name, nil, &size, nil, 0) != 0 || size == 0 {
        return "unknown"
    }
    var buffer = [CChar](repeating: 0, count: size)
    if sysctlbyname(name, &buffer, &size, nil, 0) != 0 {
        return "unknown"
    }
    return String(cString: buffer)
}

func cCharTupleString<T>(_ tuple: T) -> String {
    var mutable = tuple
    return withUnsafeBytes(of: &mutable) { rawBuffer in
        let bytes = rawBuffer.prefix { $0 != 0 }
        return String(decoding: bytes, as: UTF8.self)
    }
}

func currentBuildInfo() -> BuildInfo {
    let version = ProcessInfo.processInfo.operatingSystemVersion
    var uts = utsname()
    uname(&uts)
    return BuildInfo(
        productVersion: "\(version.majorVersion).\(version.minorVersion).\(version.patchVersion)",
        buildVersion: sysctlString("kern.osversion"),
        darwinVersion: cCharTupleString(uts.release),
        architecture: cCharTupleString(uts.machine)
    )
}

let candidates = [
    "/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight",
    "/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/SkyLight",
]

let cSymbols = [
    "SLSMainConnectionID",
    "CGSMainConnectionID",
    "SLSNewConnection",
    "SLSReleaseConnection",
    "SLSCopyManagedDisplays",
    "SLSCopyManagedDisplaySpaces",
    "SLSCopySpacesForWindows",
    "SLSCopyWindowsWithOptionsAndTags",
    "SLSGetActiveSpace",
    "SLSManagedDisplayGetCurrentSpace",
    "SLSSpaceGetType",
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
]

let objcClasses = [
    "SLContentFilter",
    "SLContentStream",
    "SLSEventAuthenticationMessage",
    "SLSSkyLightEventAuthenticationMessage",
    "SLSSkyLightKeyEventAuthenticationMessage",
    "SLSBridgedCopyManagedDisplaySpacesOperation",
    "SLSBridgedCopySpacesForWindowsOperation",
    "SLSBridgedMoveWindowsToManagedSpaceOperation",
    "SLSBridgedSpaceSetAbsoluteLevelOperation",
    "SLWindowMirroringManager",
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

var records: [ProbeRecord] = []
for symbol in cSymbols.sorted() {
    let ptr = dlsym(handle, symbol)
    records.append(
        ProbeRecord(kind: "c_symbol", name: symbol, status: ptr == nil ? "missing" : "present")
    )
}
for className in objcClasses.sorted() {
    let cls: AnyClass? = NSClassFromString(className)
    records.append(
        ProbeRecord(kind: "objc_class", name: className, status: cls == nil ? "missing" : "present")
    )
}

let buildInfo = currentBuildInfo()

if jsonOutput {
    var byKind: [String: [String: Int]] = [:]
    for record in records {
        var counts = byKind[record.kind] ?? [:]
        counts[record.status, default: 0] += 1
        byKind[record.kind] = counts
    }
    let summary = ProbeSummary(
        present: records.filter { $0.status == "present" }.count,
        missing: records.filter { $0.status == "missing" }.count,
        byKind: byKind
    )
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    let data = try encoder.encode(
        ProbeReport(
            schemaVersion: 1,
            build: buildInfo,
            loadedPath: loadedPath ?? "unknown",
            summary: summary,
            records: records
        )
    )
    FileHandle.standardOutput.write(data)
    print("")
} else {
    print("loaded_path\t\(loadedPath ?? "unknown")")
    print("product_version\t\(buildInfo.productVersion)")
    print("build_version\t\(buildInfo.buildVersion)")
    print("darwin_version\t\(buildInfo.darwinVersion)")
    print("architecture\t\(buildInfo.architecture)")
    print("kind\tname\tstatus")
    for record in records {
        print("\(record.kind)\t\(record.name)\t\(record.status)")
    }
}
