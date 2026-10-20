import AppKit
@main struct WorkspaceCheck {
    static func near(_ a:CGFloat,_ b:CGFloat) {precondition(abs(a-b)<0.00001,"\(a) != \(b)")}
    static func point(_ a:NSPoint,_ b:NSPoint) {near(a.x,b.x);near(a.y,b.y)}
    static func main() throws {
        NSApplication.shared.setActivationPolicy(.prohibited)
        var camera=StageViewport(bounds:NSRect(x:10,y:20,width:800,height:600),scale:2,pan:NSPoint(x:31,y:-23))
        let world=NSPoint(x:-42,y:87),anchor=NSPoint(x:170,y:230)
        point(camera.viewToWorld(camera.worldToView(world)),world)
        let fixed=camera.viewToWorld(anchor)
        camera.zoom(by:3,at:anchor);point(camera.viewToWorld(anchor),fixed)
        camera.zoom(by:1000,at:anchor);near(camera.scale,12);point(camera.viewToWorld(anchor),fixed)
        camera.zoom(by:0.000001,at:anchor);near(camera.scale,0.1);point(camera.viewToWorld(anchor),fixed)
        let art=NSRect(x:-120,y:250,width:180,height:300)
        camera.fit(worldBounds:art)
        point(camera.worldToView(NSPoint(x:art.midX,y:art.midY)),NSPoint(x:camera.bounds.midX,y:camera.bounds.midY))
        let corner=camera.worldToView(NSPoint(x:art.minX,y:art.minY))
        precondition(corner.x>=camera.bounds.minX+47.99 && corner.y>=camera.bounds.minY+47.99)
        let editor=Editor()
        editor.window=RigWindow(contentRect:.zero,styleMask:[],backing:.buffered,defer:false)
        editor.history.groupsByEvent=false;editor.stage.owner=editor
        editor.stage.frame=NSRect(x:0,y:0,width:600,height:500)
        editor.selected=1;editor.project.bones[0].angle=67
        let initial=editor.project
        let origins=editor.stage.transforms(initial).map {$0.transform(NSPoint.zero)}
        editor.beginCanvasEdit()
        editor.stage.moveSelectedBone(worldDelta:NSPoint(x:20,y:99),axis:.x)
        let moved=editor.stage.transforms(editor.project).map {$0.transform(NSPoint.zero)}
        point(moved[1],NSPoint(x:origins[1].x+20,y:origins[1].y))
        point(moved[2],NSPoint(x:origins[2].x+20,y:origins[2].y))
        point(moved[8],origins[8]);precondition(editor.project.frames == initial.frames)
        editor.finishCanvasEdit();editor.history.undo();precondition(editor.project==initial)
        precondition(!editor.history.canUndo)
        editor.stage.pan=NSPoint(x:20,y:-31);editor.zoom=4
        let origin=editor.stage.gizmoOrigin()!
        precondition(editor.stage.gizmoHit(at:NSPoint(x:origin.x+40,y:origin.y)) == .x)
        precondition(editor.stage.gizmoHit(at:NSPoint(x:origin.x,y:origin.y+40)) == .y)
        precondition(editor.stage.gizmoHit(at:origin) == .free)
        let slider=PropertySlider(value:0,minValue:-180,maxValue:180,target:nil,action:nil)
        slider.identifier=NSUserInterfaceItemIdentifier("Angle");editor.propertySliders["Angle"]=slider
        editor.clearHistory();editor.beginSliderEdit()
        for value in [15.0,30,45] {slider.doubleValue=value;editor.sliderChanged(slider)}
        editor.finishSliderEdit("Angle");precondition(editor.project.bones[1].angle==45)
        editor.history.undo();precondition(editor.project==initial && !editor.history.canUndo)
        editor.history.redo();precondition(editor.project.bones[1].angle==45)
        editor.project.bones[1].angle=720;editor.refreshFields();precondition(slider.maxValue>=720 && slider.doubleValue==720)
        editor.stage.frame=NSRect(x:0,y:0,width:100,height:100);editor.zoom=12;editor.stage.pan = .zero
        let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:200,pixelsHigh:200,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
        let context=NSGraphicsContext(bitmapImageRep:bitmap)!
        NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=context
        NSColor.white.setFill();NSRect(x:0,y:0,width:200,height:200).fill()
        context.cgContext.translateBy(x:50,y:50)
        editor.stage.draw(editor.stage.bounds)
        NSGraphicsContext.restoreGraphicsState()
        var changed=0
        for y in 0..<200 {for x in 0..<200 {
            let c=bitmap.colorAt(x:x,y:y)!.usingColorSpace(.deviceRGB)!
            let white=c.redComponent>0.99 && c.greenComponent>0.99 && c.blueComponent>0.99
            if x<50 || x>=150 || y<50 || y>=150 {precondition(white,"preview escaped workspace at \(x),\(y)")}
            else if !white {changed+=1}
        }}
        precondition(changed>9000)
        print("PASS workspace: cursor zoom and limits, Fit, rotated-parent axis with descendants, gizmo hit, slider undo/redo and expanded range, actual preview clipping")
    }
}
