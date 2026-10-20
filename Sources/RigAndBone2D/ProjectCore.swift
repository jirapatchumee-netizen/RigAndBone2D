import AppKit
enum ProjectCore {
    static func drawOrder(_ project: Project) -> [Int] {
        project.bones.indices.sorted {
            project.bones[$0].layer == project.bones[$1].layer ? $0 < $1 : project.bones[$0].layer < project.bones[$1].layer
        }
    }
    static func validate(_ p:Project)throws {
        func fail()throws{throw RigError(code:"validation_failed",message:"Invalid project: check bone hierarchy, dimensions, and keyframes.")}
        if p.version != 1 || p.bones.isEmpty || p.bones.count>512 || !p.duration.isFinite || p.duration<=0 || p.duration>120 {try fail()}
        let ids=p.bones.enumerated().map { $0.element.id ?? "bone-\($0.offset)" }
        if ids.contains(where:{$0.isEmpty}) || Set(ids).count != ids.count {throw RigError(code:"duplicate_id",message:"Bone IDs must be nonempty and unique")}
        if Set(p.frames.map(\.time)).count != p.frames.count {throw RigError(code:"duplicate_time",message:"Keyframe times must be unique")}
        for (i,b) in p.bones.enumerated(){if let parent=b.parent,parent<0 || parent>=i {try fail()};if b.color.count != 3 || !([b.x,b.y,b.length,b.width,b.angle,b.pivotX,b.pivotY,b.imageOffsetX ?? 0,b.imageOffsetY ?? 0]+b.color).allSatisfy({$0.isFinite}) || b.length<=0 || b.width<=0 || !(0...1).contains(b.pivotX) || !(0...1).contains(b.pivotY) || !b.color.allSatisfy({(0...1).contains($0)}) {try fail()}}
        for f in p.frames {if !f.time.isFinite || f.time<0 || f.time>p.duration || f.angles.count != p.bones.count || !f.angles.allSatisfy({$0.isFinite}) {try fail()}}
    }
    static func sample(_ project: inout Project, time t: Double) {
        let frames=project.frames.sorted{$0.time<$1.time}
        guard let first=frames.first else{return}
        let a=frames.last(where:{$0.time<=t}) ?? first
        let b=frames.first(where:{$0.time>=t}) ?? frames.last!
        let u=b.time>a.time ? (t-a.time)/(b.time-a.time) : 0
        for i in project.bones.indices {project.bones[i].angle=a.angles[i]+(b.angles[i]-a.angles[i])*u}
    }
    static func save(_ project: Project, to url: URL, expectedRevision: String? = nil) throws {
        try ProjectStore.save(project,to:url,expectedRevision:expectedRevision)
    }
    static func render(_ project: Project, to url: URL, sheet: Bool) throws {
        let cell=384,columns=sheet ? 6 : 1,rows=sheet ? 4 : 1,count=sheet ? 24 : 1
        guard let bitmap=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:cell*columns,pixelsHigh:cell*rows,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0),let context=NSGraphicsContext(bitmapImageRep:bitmap) else {throw NSError(domain:"Renderer",code:1)}
        NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(cgContext:context.cgContext,flipped:true)
        defer {NSGraphicsContext.restoreGraphicsState()}
        let ctx=context.cgContext;ctx.clear(CGRect(x:0,y:0,width:cell*columns,height:cell*rows));ctx.translateBy(x:0,y:CGFloat(cell*rows));ctx.scaleBy(x:1,y:-1)
        let stage=Stage();var pose=project
        for i in 0..<count {
            if sheet {sample(&pose,time:Double(i)/Double(count)*project.duration)}
            ctx.saveGState();let x=CGFloat(i%columns*cell),y=CGFloat(i/columns*cell)
            ctx.clip(to:CGRect(x:x,y:y,width:CGFloat(cell),height:CGFloat(cell)))
            stage.drawRig(pose,center:NSPoint(x:x+192,y:y+192),scale:1,overlays:false);ctx.restoreGState()
        }
        guard let data=bitmap.representation(using:.png,properties:[:]) else {throw NSError(domain:"Renderer",code:2)}
        try data.write(to:url,options:.atomic)
    }
}
