#!/usr/bin/env swift
import Darwin
import Foundation

struct ProbeRecord: Encodable {
    let kind: String
    let name: String
    let status: String
    let imagePath: String?
    let resolvedSymbol: String?
    let address: String?
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

struct Options {
    var images: [String] = []
    var symbols: [String] = []
    var classes: [String] = []
    var jsonOutput = false
    var includeAddresses = false
    var redactHome = true
}

enum ParseError: Error, CustomStringConvertible {
    case message(String)

    var description: String {
        switch self {
        case .message(let value):
            value
        }
    }
}

func usage() -> String {
    """
    Usage: dlopen_symbol_probe.swift --image PATH [options]

    Read-only dlopen/dlsym/NSClassFromString probe for any local framework or dylib.

    Options:
      --image PATH          Image path or install name to dlopen. Repeat for fallback paths.
      --symbol NAME         C symbol to probe with dlsym. Repeat as needed.
      --symbol-file PATH    Newline-delimited C symbol names. # comments allowed.
      --class NAME          Objective-C class to probe with NSClassFromString. Repeat as needed.
      --class-file PATH     Newline-delimited Objective-C class names. # comments allowed.
      --json                Emit JSON instead of TSV.
      --addresses           Include raw resolved addresses in JSON/TSV.
      --no-redact-home      Do not replace the current home directory with ~ in paths.
      -h, --help            Show this help.
    """
}

func readNames(from path: String) throws -> [String] {
    let text = try String(contentsOfFile: path, encoding: .utf8)
    return text.split(separator: "\n").compactMap { rawLine in
        let line = rawLine.split(separator: "#", maxSplits: 1).first.map(String.init) ?? ""
        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}

func parseOptions(_ arguments: [String]) throws -> Options {
    var options = Options()
    var index = 1
    while index < arguments.count {
        let arg = arguments[index]
        switch arg {
        case "-h", "--help":
            print(usage())
            exit(0)
        case "--image":
            index += 1
            guard index < arguments.count else { throw ParseError.message("--image requires a path") }
            options.images.append(arguments[index])
        case "--symbol":
            index += 1
            guard index < arguments.count else { throw ParseError.message("--symbol requires a name") }
            options.symbols.append(arguments[index])
        case "--symbol-file":
            index += 1
            guard index < arguments.count else { throw ParseError.message("--symbol-file requires a path") }
            options.symbols.append(contentsOf: try readNames(from: arguments[index]))
        case "--class":
            index += 1
            guard index < arguments.count else { throw ParseError.message("--class requires a name") }
            options.classes.append(arguments[index])
        case "--class-file":
            index += 1
            guard index < arguments.count else { throw ParseError.message("--class-file requires a path") }
            options.classes.append(contentsOf: try readNames(from: arguments[index]))
        case "--json":
            options.jsonOutput = true
        case "--addresses":
            options.includeAddresses = true
        case "--no-redact-home":
            options.redactHome = false
        default:
            throw ParseError.message("unknown argument: \(arg)")
        }
        index += 1
    }
    if options.images.isEmpty {
        throw ParseError.message("at least one --image path is required")
    }
    if options.symbols.isEmpty && options.classes.isEmpty {
        throw ParseError.message("provide at least one --symbol, --symbol-file, --class, or --class-file")
    }
    options.symbols = Array(Set(options.symbols)).sorted()
    options.classes = Array(Set(options.classes)).sorted()
    return options
}

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

func redactPath(_ path: String?, redactHome: Bool) -> String? {
    guard let path, redactHome else { return path }
    let home = FileManager.default.homeDirectoryForCurrentUser.path
    if path == home {
        return "~"
    }
    if path.hasPrefix(home + "/") {
        return "~" + path.dropFirst(home.count)
    }
    return path
}

func pointerAddress(_ pointer: UnsafeMutableRawPointer?) -> String? {
    guard let pointer else { return nil }
    return String(format: "0x%llx", UInt64(UInt(bitPattern: pointer)))
}

func symbolRecord(
    handle: UnsafeMutableRawPointer,
    name: String,
    includeAddress: Bool,
    redactHome: Bool
) -> ProbeRecord {
    guard let pointer = dlsym(handle, name) else {
        return ProbeRecord(
            kind: "c_symbol",
            name: name,
            status: "missing",
            imagePath: nil,
            resolvedSymbol: nil,
            address: nil
        )
    }
    var info = Dl_info()
    let hasInfo = dladdr(pointer, &info) != 0
    let imagePath = hasInfo && info.dli_fname != nil ? String(cString: info.dli_fname) : nil
    let resolvedSymbol = hasInfo && info.dli_sname != nil ? String(cString: info.dli_sname) : nil
    return ProbeRecord(
        kind: "c_symbol",
        name: name,
        status: "present",
        imagePath: redactPath(imagePath, redactHome: redactHome),
        resolvedSymbol: resolvedSymbol,
        address: includeAddress ? pointerAddress(pointer) : nil
    )
}

func classRecord(name: String, redactHome: Bool) -> ProbeRecord {
    guard let cls = NSClassFromString(name) else {
        return ProbeRecord(
            kind: "objc_class",
            name: name,
            status: "missing",
            imagePath: nil,
            resolvedSymbol: nil,
            address: nil
        )
    }
    return ProbeRecord(
        kind: "objc_class",
        name: name,
        status: "present",
        imagePath: redactPath(Bundle(for: cls).bundlePath, redactHome: redactHome),
        resolvedSymbol: nil,
        address: nil
    )
}

do {
    let options = try parseOptions(CommandLine.arguments)
    var handle: UnsafeMutableRawPointer?
    var loadedPath: String?
    for image in options.images {
        if let h = dlopen(image, RTLD_LAZY | RTLD_LOCAL) {
            handle = h
            loadedPath = image
            break
        }
    }
    guard let handle else {
        fputs("error: failed to dlopen any --image path\n", stderr)
        exit(1)
    }
    defer { dlclose(handle) }

    let records =
        options.symbols.map {
            symbolRecord(
                handle: handle,
                name: $0,
                includeAddress: options.includeAddresses,
                redactHome: options.redactHome
            )
        }
        + options.classes.map { classRecord(name: $0, redactHome: options.redactHome) }
    let buildInfo = currentBuildInfo()

    if options.jsonOutput {
        var byKind: [String: [String: Int]] = [:]
        for record in records {
            var counts = byKind[record.kind] ?? [:]
            counts[record.status, default: 0] += 1
            byKind[record.kind] = counts
        }
        let report = ProbeReport(
            schemaVersion: 1,
            build: buildInfo,
            loadedPath: redactPath(loadedPath, redactHome: options.redactHome) ?? "unknown",
            summary: ProbeSummary(
                present: records.filter { $0.status == "present" }.count,
                missing: records.filter { $0.status == "missing" }.count,
                byKind: byKind
            ),
            records: records
        )
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        FileHandle.standardOutput.write(try encoder.encode(report))
        print("")
    } else {
        print("loaded_path\t\(redactPath(loadedPath, redactHome: options.redactHome) ?? "unknown")")
        print("product_version\t\(buildInfo.productVersion)")
        print("build_version\t\(buildInfo.buildVersion)")
        print("darwin_version\t\(buildInfo.darwinVersion)")
        print("architecture\t\(buildInfo.architecture)")
        print("kind\tname\tstatus\timage_path\tresolved_symbol\taddress")
        for record in records {
            print(
                "\(record.kind)\t\(record.name)\t\(record.status)\t\(record.imagePath ?? "")\t\(record.resolvedSymbol ?? "")\t\(record.address ?? "")"
            )
        }
    }
} catch {
    fputs("error: \(error)\n\n\(usage())\n", stderr)
    exit(2)
}
