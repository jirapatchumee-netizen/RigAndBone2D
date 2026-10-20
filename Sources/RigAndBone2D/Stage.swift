import AppKit
struct StageViewport {
    var bounds: NSRect
    var scale: CGFloat
    var pan: NSPoint = .zero
    var center: NSPoint { NSPoint(x:bounds.midX+pan.x,y:bounds.midY+pan.y) }
    func worldToView(_ p:NSPoint)->NSPoint {NSPoint(x:center.x+p.x*scale,y:center.y+p.y*scale)}
    func viewToWorld(_ p:NSPoint)->NSPoint {NSPoint(x:(p.x-center.x)/scale,y:(p.y-center.y)/scale)}
    mutating func zoom(by factor:CGFloat,at anchor:NSPoint) {
        let world=viewToWorld(anchor)
        scale=max(0.1,min(12,scale*factor))
        pan=NSPoint(x:anchor.x-bounds.midX-world.x*scale,y:anchor.y-bounds.midY-world.y*scale)
    }
    mutating func fit(worldBounds:NSRect,padding:CGFloat=48) {
        guard !worldBounds.isNull,worldBounds.width>0,worldBounds.height>0 else{return}
        scale=max(0.1,min(12,min(max(1,bounds.width-padding*2)/worldBounds.width,max(1,bounds.height-padding*2)/worldBounds.height)))
        pan=NSPoint(x:-worldBounds.midX*scale,y:-worldBounds.midY*scale)
    }
}
enum RigAxis {case x,y,free}
class Stage: NSView {
    weak var owner: Editor?
    var dragStart = NSPoint.zero
    var imageDragIndex: Int?
    var boneDragIndex:Int?
    var axisDrag:RigAxis?
    var panStart:NSPoint?
    var pan=NSPoint.zero
    var viewport:StageViewport {StageViewport(bounds:bounds,scale:owner?.zoom ?? 1,pan:pan)}
    func cancelDrag() {imageDragIndex=nil;boneDragIndex=nil;axisDrag=nil;panStart=nil}
    func setViewport(_ camera:StageViewport) {owner?.zoom=camera.scale;pan=camera.pan;needsDisplay=true}
    func zoom(by factor:CGFloat,at anchor:NSPoint) {var camera=viewport;camera.zoom(by:factor,at:anchor);setViewport(camera)}
    func artworkBounds(_ project:Project)->NSRect {
        let ts=transforms(project)
        return project.bones.indices.reduce(NSRect.null) { result,i in
            let b=project.bones[i]
            guard b.visible != false else{return result}
            let r=b.image != nil ? b.imageRect : NSRect(x:-b.width/2,y:-b.width*0.12,width:b.width,height:b.length+b.width*0.12)
            let points=[NSPoint(x:r.minX,y:r.minY),NSPoint(x:r.maxX,y:r.minY),NSPoint(x:r.minX,y:r.maxY),NSPoint(x:r.maxX,y:r.maxY)].map {ts[i].transform($0)}
            let box=NSRect(x:points.map(\.x).min()!,y:points.map(\.y).min()!,width:points.map(\.x).max()!-points.map(\.x).min()!,height:points.map(\.y).max()!-points.map(\.y).min()!)
            return result.union(box)
        }
    }
    func fitArtwork() {guard let owner else{return};var camera=viewport;camera.fit(worldBounds:artworkBounds(owner.project));setViewport(camera)}
    func gizmoOrigin()->NSPoint? {
        guard let o=owner,o.showBones,!o.moveImageMode,o.project.bones.indices.contains(o.selected) else{return nil}
        return viewport.worldToView(transforms(o.project)[o.selected].transform(.zero))
    }
    func gizmoHit(at p:NSPoint)->RigAxis? {
        guard let a=gizmoOrigin() else{return nil}
        if abs(p.x-a.x)<=9 && abs(p.y-a.y)<=9 {return .free}
        if p.x>=a.x+12 && p.x<=a.x+62 && abs(p.y-a.y)<=9 {return .x}
        if p.y>=a.y+12 && p.y<=a.y+62 && abs(p.x-a.x)<=9 {return .y}
        return nil
    }
    func moveSelectedBone(worldDelta:NSPoint,axis:RigAxis = .free) {
        guard let o=owner,o.project.bones.indices.contains(o.selected) else{return}
        let i=o.selected,ts=transforms(o.project)
        let angle=o.project.bones[i].parent.map {atan2(ts[$0].m12,ts[$0].m11)} ?? 0
        let dx=axis == .y ? 0 : worldDelta.x,dy=axis == .x ? 0 : worldDelta.y
        o.project.bones[i].x += dx*cos(angle)+dy*sin(angle)
        o.project.bones[i].y += -dx*sin(angle)+dy*cos(angle)
    }
    func drawGizmo() {
        guard let a=gizmoOrigin() else{return}
        for (axis,color,label) in [(RigAxis.x,NSColor.systemRed,"X"),(.y,NSColor.systemGreen,"Y")] {
            let end=NSPoint(x:a.x+(axis == .x ? 58 : 0),y:a.y+(axis == .y ? 58 : 0))
            let line=NSBezierPath();line.move(to:a);line.line(to:end);line.lineWidth=3;color.setStroke();line.stroke()
            let arrow=NSBezierPath();arrow.move(to:end)
            arrow.line(to:NSPoint(x:end.x-(axis == .x ? 9 : 5),y:end.y-(axis == .y ? 9 : 5)))
            arrow.line(to:NSPoint(x:end.x-(axis == .x ? 9 : -5),y:end.y-(axis == .y ? 9 : -5)));arrow.close();color.setFill();arrow.fill()
            label.draw(at:NSPoint(x:end.x+5,y:end.y+3),withAttributes:[.font:NSFont.boldSystemFont(ofSize:11),.foregroundColor:color])
        }
        NSColor.windowBackgroundColor.setFill();NSBezierPath(rect:NSRect(x:a.x-6,y:a.y-6,width:12,height:12)).fill()
        NSColor.white.setStroke();NSBezierPath(rect:NSRect(x:a.x-6,y:a.y-6,width:12,height:12)).stroke()
    }
    override var isFlipped: Bool { true }
    override var acceptsFirstResponder: Bool { true }
    func transforms(_ project: Project) -> [AffineTransform] {
        var result: [AffineTransform] = []
        for (i,b) in project.bones.enumerated() {
            let p = (b.parent != nil && b.parent! < i) ? result[b.parent!] : AffineTransform()
            let c=cos(radians(b.angle)),s=sin(radians(b.angle))
            let origin=p.transform(NSPoint(x:b.x,y:b.y))
            let t=AffineTransform(m11:p.m11*c+p.m21*s,m12:p.m12*c+p.m22*s,m21:-p.m11*s+p.m21*c,m22:-p.m12*s+p.m22*c,tX:origin.x,tY:origin.y)
            result.append(t)
        }
        return result
    }
    override func draw(_ dirtyRect: NSRect) {
        NSGraphicsContext.saveGraphicsState()
        defer {NSGraphicsContext.restoreGraphicsState()}
        NSBezierPath(rect:bounds).addClip()
        NSColor(calibratedRed:0.055,green:0.075,blue:0.12,alpha:1).setFill(); bounds.fill()
        guard let owner else { return }
        let grid = NSBezierPath()
        for x in stride(from:CGFloat(0),through:bounds.width,by:32) { grid.move(to:NSPoint(x:x,y:0));grid.line(to:NSPoint(x:x,y:bounds.height)) }
        for y in stride(from:CGFloat(0),through:bounds.height,by:32) { grid.move(to:NSPoint(x:0,y:y));grid.line(to:NSPoint(x:bounds.width,y:y)) }
        NSColor(white:1,alpha:0.04).setStroke();grid.stroke()
        drawRig(owner.project, center:viewport.center, scale:viewport.scale, overlays:owner.showBones)
        drawGizmo()
        let text = owner.moveImageMode ? "Drag artwork to adjust overlap · Bone joints stay fixed" : "Wheel zoom · Middle-drag pan · X/Y handles move rig · Drag bone to rotate"
        text.draw(at:NSPoint(x:20,y:bounds.height-30),withAttributes:[.font:NSFont.systemFont(ofSize:12),.foregroundColor:NSColor.secondaryLabelColor])
    }
    func drawRig(_ project: Project, center: NSPoint, scale: CGFloat, overlays: Bool) {
        let ts = transforms(project)
        for i in ProjectCore.drawOrder(project) {
            let b = project.bones[i]
            if b.visible == false {continue}
            NSGraphicsContext.saveGraphicsState()
            let t=ts[i]
            NSGraphicsContext.current!.cgContext.concatenate(CGAffineTransform(a:scale*t.m11,b:scale*t.m12,c:scale*t.m21,d:scale*t.m22,tx:center.x+scale*t.tX,ty:center.y+scale*t.tY))
            if let data=b.image, let img=NSImage(data:data) {
                img.draw(in:b.imageRect,from:.zero,operation:.sourceOver,fraction:1,respectFlipped:true,hints:nil)
                if owner?.moveImageMode == true,owner?.selected == i {
                    NSColor.systemYellow.setStroke()
                    let outline=NSBezierPath(rect:b.imageRect);outline.lineWidth=1/scale;outline.stroke()
                }
            } else {
                let r = NSRect(x:-b.width/2,y:-b.width*0.12,width:b.width,height:b.length+b.width*0.12)
                let p = NSBezierPath(roundedRect:r,xRadius:b.width*0.35,yRadius:b.width*0.35)
                NSColor(calibratedRed:b.color[0],green:b.color[1],blue:b.color[2],alpha:1).setFill();p.fill()
                NSColor(white:0,alpha:0.35).setStroke();p.lineWidth=2;p.stroke()
            }
            NSGraphicsContext.restoreGraphicsState()
        }
        if overlays {
            for i in project.bones.indices {
                let b=project.bones[i], a=ts[i].transform(NSPoint.zero), z=ts[i].transform(NSPoint(x:0,y:b.length))
                func s(_ p:NSPoint)->NSPoint { NSPoint(x:center.x+p.x*scale,y:center.y+p.y*scale) }
                let p=NSBezierPath();p.move(to:s(a));p.line(to:s(z));p.lineWidth = i == owner?.selected ? 3 : 1.5
                (i == owner?.selected ? NSColor.systemYellow : NSColor.systemTeal).setStroke();p.stroke()
                let dot=NSBezierPath(ovalIn:NSRect(x:s(a).x-4,y:s(a).y-4,width:8,height:8));NSColor.systemYellow.setFill();dot.fill()
            }
        }
    }
    override func mouseDown(with event:NSEvent) {
        guard let o=owner else{return};let p=convert(event.locationInWindow,from:nil);dragStart=p
        window?.makeFirstResponder(self);cancelDrag()
        if let axis=gizmoHit(at:p) {o.stop();axisDrag=axis;boneDragIndex=o.selected;o.beginCanvasEdit();return}
        let ts=transforms(o.project)
        if o.moveImageMode {
            let q=viewport.viewToWorld(p)
            func hitsImage(_ i:Int)->Bool {
                let b=o.project.bones[i]
                guard b.visible != false,b.image != nil else{return false}
                var inverse=ts[i];inverse.invert()
                return b.imageRect.contains(inverse.transform(q))
            }
            let ordered=ProjectCore.drawOrder(o.project).reversed()
            if o.project.bones.indices.contains(o.selected),hitsImage(o.selected) {imageDragIndex=o.selected}
            else {imageDragIndex=ordered.first(where:hitsImage)}
            if let i=imageDragIndex {o.stop();o.selected=i;o.refresh();o.beginCanvasEdit()}
            return
        }
        let distances=o.project.bones.indices.map { i -> (Int,Double) in
            let b=o.project.bones[i];let a=ts[i].transform(NSPoint.zero),z=ts[i].transform(NSPoint(x:0,y:b.length))
            let q=viewport.viewToWorld(p)
            let dx=z.x-a.x,dy=z.y-a.y;let u=max(0,min(1,((q.x-a.x)*dx+(q.y-a.y)*dy)/max(1,dx*dx+dy*dy)))
            return(i,hypot(q.x-a.x-u*dx,q.y-a.y-u*dy))
        }
        if let closest=distances.min(by:{$0.1<$1.1}),closest.1<35 {o.stop();o.selected=closest.0;boneDragIndex=closest.0;o.refresh();o.beginCanvasEdit()}
    }
    override func mouseDragged(with event:NSEvent) {
        guard let o=owner, o.project.bones.indices.contains(o.selected) else{return}
        o.stop();let p=convert(event.locationInWindow,from:nil),i=o.selected
        if let axis=axisDrag {
            moveSelectedBone(worldDelta:NSPoint(x:(p.x-dragStart.x)/viewport.scale,y:(p.y-dragStart.y)/viewport.scale),axis:axis)
        } else if o.moveImageMode {
            guard imageDragIndex == i else{return}
            let t=transforms(o.project)[i]
            let delta=NSPoint(x:(p.x-dragStart.x)/o.zoom,y:(p.y-dragStart.y)/o.zoom)
            o.project.bones[i].moveImage(worldDelta:delta,worldAngle:atan2(t.m12,t.m11))
        } else if boneDragIndex != i {return
        } else if event.modifierFlags.contains(.shift) {
            moveSelectedBone(worldDelta:NSPoint(x:(p.x-dragStart.x)/viewport.scale,y:(p.y-dragStart.y)/viewport.scale))
        } else {
            let ts=transforms(o.project),a=ts[i].transform(NSPoint.zero)
            let q=viewport.viewToWorld(p)
            let global=atan2(q.y-a.y,q.x-a.x)*180 / .pi-90
            let parent=o.project.bones[i].parent.map { atan2(ts[$0].m12,ts[$0].m11)*180 / .pi } ?? 0
            o.project.bones[i].angle=global-parent
        }
        dragStart=p;o.refresh()
    }
    override func mouseUp(with event:NSEvent) {owner?.finishCanvasEdit();cancelDrag()}
    override func scrollWheel(with event:NSEvent) {
        guard axisDrag == nil,imageDragIndex == nil,boneDragIndex == nil,panStart == nil else{return}
        let amount=event.hasPreciseScrollingDeltas ? event.scrollingDeltaY*0.01 : event.scrollingDeltaY*0.12
        zoom(by:exp(max(-1,min(1,amount))),at:convert(event.locationInWindow,from:nil))
    }
    override func otherMouseDown(with event:NSEvent) {
        guard event.buttonNumber == 2 else{super.otherMouseDown(with:event);return}
        window?.makeFirstResponder(self);cancelDrag();panStart=convert(event.locationInWindow,from:nil)
    }
    override func otherMouseDragged(with event:NSEvent) {
        guard event.buttonNumber == 2,let previous=panStart else{return}
        let p=convert(event.locationInWindow,from:nil)
        pan.x += p.x-previous.x;pan.y += p.y-previous.y;panStart=p;needsDisplay=true
    }
    override func otherMouseUp(with event:NSEvent) {panStart=nil}
    override func keyDown(with event:NSEvent) {if event.keyCode==49 {owner?.play()} else {super.keyDown(with:event)} }
}

