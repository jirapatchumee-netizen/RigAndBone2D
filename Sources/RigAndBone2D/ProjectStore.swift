import Foundation
import CryptoKit
import Darwin

/// All participating writers lock the same sidecar before revision check + atomic replace.
enum ProjectStore {
    static func revision(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
    static func load(_ url: URL) throws -> (project: Project, revision: String) {
        let data = try Data(contentsOf: url)
        var project = try JSONDecoder().decode(Project.self, from: data)
        for i in project.bones.indices where project.bones[i].id == nil { project.bones[i].id = "bone-\(i)" }
        try ProjectCore.validate(project)
        return (project, revision(data))
    }
    @discardableResult
    static func save(_ project: Project, to url: URL, expectedRevision: String? = nil, createOnly: Bool = false) throws -> String {
        var project = project
        for i in project.bones.indices where project.bones[i].id == nil { project.bones[i].id = "bone-\(i)" }
        try ProjectCore.validate(project)
        let encoder = JSONEncoder(); encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(project)
        // Resolve aliases so GUI and CLI use one lock for symlinked paths.
        let destination = url.resolvingSymlinksInPath().standardizedFileURL
        let lockURL = destination.deletingLastPathComponent().appendingPathComponent(".\(destination.lastPathComponent).lock")
        let descriptor = Darwin.open(lockURL.path, O_CREAT | O_RDWR, mode_t(0o600))
        guard descriptor >= 0 else { throw RigError(code: "write_failed", message: "Cannot open project lock", context: lockURL.path) }
        defer { Darwin.close(descriptor) }
        guard flock(descriptor, LOCK_EX) == 0 else { throw RigError(code: "write_failed", message: "Cannot lock project", context: destination.path) }
        defer { flock(descriptor, LOCK_UN) }
        let exists = FileManager.default.fileExists(atPath: destination.path)
        if createOnly && exists { throw RigError(code: "already_exists", message: "Project exists; explicit replacement is required", context: destination.path) }
        if let expected = expectedRevision {
            guard exists, try revision(Data(contentsOf: destination)) == expected else {
                throw RigError(code: "revision_conflict", message: "Project changed. Inspect or reopen it before editing again", context: destination.path)
            }
        }
        try data.write(to: destination, options: .atomic)
        return revision(data)
    }
}
