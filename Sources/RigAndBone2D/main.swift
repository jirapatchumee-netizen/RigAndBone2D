import AppKit
if CommandLine.arguments.contains("--agent") {
    AgentAPI.run()
} else {
    let app=NSApplication.shared
    app.setActivationPolicy(.regular)
    let editor=Editor();app.delegate=editor;app.run()
}
