import AppKit
@main struct HistoryCheck {
    static func main() throws {
        let app=NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let editor=Editor()
        editor.window=RigWindow(contentRect:.zero,styleMask:[],backing:.buffered,defer:false)
        editor.history.levelsOfUndo=100;editor.history.groupsByEvent=false
        editor.stage.owner=editor
        let initial=editor.project
        editor.addBone()
        precondition(editor.project.bones.count == initial.bones.count+1)
        editor.history.undo();precondition(editor.project == initial)
        editor.history.redo();precondition(editor.project.bones.count == initial.bones.count+1)
        editor.history.undo()
        editor.beginCanvasEdit()
        for _ in 0..<12 {editor.project.bones[1].angle += 1}
        editor.finishCanvasEdit()
        editor.history.undo();precondition(editor.project == initial)
        precondition(!editor.history.canUndo)
        editor.history.redo();precondition(editor.project.bones[1].angle == initial.bones[1].angle+12)
        editor.history.undo()
        editor.beginCanvasEdit();editor.finishCanvasEdit();precondition(!editor.history.canUndo)
        let before=editor.snapshot()
        editor.project.bones[1].name="New edit"
        editor.record(before,"Rename")
        precondition(!editor.history.canRedo)
        editor.loadedRevision="latest-revision"
        editor.loadedURL=URL(fileURLWithPath:"/tmp/snapshot-only.rig2d")
        editor.history.undo()
        precondition(editor.loadedRevision == "latest-revision")
        precondition(editor.loadedURL?.path == "/tmp/snapshot-only.rig2d")
        for i in 0..<110 {
            let before=editor.snapshot();editor.project.bones[1].x=Double(i+1);editor.record(before,"Move")
        }
        var count=0
        while editor.history.canUndo {editor.history.undo();count+=1}
        precondition(count == 100)
        editor.clearHistory();precondition(!editor.history.canUndo && !editor.history.canRedo)
        print("PASS native AppKit history: add/undo/redo, drag grouping, no-op, redo invalidation, revision isolation, 100-action bound, clear")
    }
}
