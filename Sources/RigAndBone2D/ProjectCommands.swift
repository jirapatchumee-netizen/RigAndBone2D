import AppKit

enum ProjectCommands {
    static let mutations: Set<String> = ["set_bone", "reorder_layers", "add_bone", "delete_bone", "import_image", "replace_image", "keyframe", "set_duration", "delete_keyframe", "clear_keyframes"]
    static func boneIndex(_ selector: Any?, in project: Project) throws -> Int {
        if let id = selector as? String, let index = project.bones.firstIndex(where: { $0.id == id }) { return index }
        if let number = selector as? NSNumber, CFGetTypeID(number) != CFBooleanGetTypeID(), number.doubleValue.isFinite,
           number.doubleValue.rounded() == number.doubleValue, number.doubleValue >= 0, number.doubleValue < Double(project.bones.count) { return number.intValue }
        throw RigError(code: "unknown_bone", message: "Use a valid bone ID or integer index")
    }
    static func subtree(_ index: Int, in project: Project) -> Set<Int> {
        var removed:Set<Int>=[index]
        for i in project.bones.indices {
            if let parent=project.bones[i].parent,removed.contains(parent) {removed.insert(i)}
        }
        return removed
    }
    static func image(_ path: String) throws -> (Data, NSSize) {
        guard ["png", "jpg", "jpeg", "tiff", "gif"].contains(URL(fileURLWithPath:path).pathExtension.lowercased()) else {
            throw RigError(code: "asset_unreadable", message: "Unsupported image extension", context: path)
        }
        let data: Data
        do { data = try Data(contentsOf: URL(fileURLWithPath: path)) }
        catch { throw RigError(code: "asset_unreadable", message: "Image file is missing or unreadable", context: path) }
        guard let image=NSImage(data:data),image.size.width.isFinite,image.size.height.isFinite,image.size.width>0,image.size.height>0 else {
            throw RigError(code: "asset_unreadable", message: "Cannot decode image", context: path)
        }
        return (data,image.size)
    }
    static func number(_ value: Any?, label: String) throws -> Double {
        guard let n=value as? NSNumber,CFGetTypeID(n) != CFBooleanGetTypeID(),n.doubleValue.isFinite else {
            throw RigError(code: "invalid_request", message: "\(label) must be a finite number")
        }
        return n.doubleValue
    }
    static func apply(_ request: [String:Any], to project: inout Project) throws {
        guard let command=request["command"] as? String,mutations.contains(command) else {throw RigError(code:"invalid_request",message:"Only project mutations are allowed in batch")}
        switch command {
        case "reorder_layers":
            guard let selectors=request["order"] as? [Any],selectors.count == project.bones.count else {
                throw RigError(code:"invalid_request",message:"order must include every bone once, front to back")
            }
            let order=try selectors.map {try boneIndex($0,in:project)}
            guard Set(order).count == project.bones.count else {
                throw RigError(code:"invalid_request",message:"order must include every bone exactly once")
            }
            for (rank,index) in order.enumerated() {project.bones[index].layer=order.count-1-rank}
        case "set_duration": project.duration=try number(request["duration"],label:"duration")
        case "clear_keyframes": project.frames=[]
        case "delete_keyframe":
            let time=try number(request["time"],label:"time");project.frames.removeAll{abs($0.time-time)<0.025}
        case "set_bone":
            let i=try boneIndex(request["bone"],in:project)
            guard var values=request["values"] as? [String:Any] else {throw RigError(code:"invalid_request",message:"values object required")}
            let allowed:Set<String>=["name","parent","x","y","length","angle","width","layer","pivotX","pivotY","imageOffsetX","imageOffsetY","color","visible"]
            guard Set(values.keys).isSubset(of:allowed) else {throw RigError(code:"invalid_request",message:"Unsupported bone property; IDs are immutable")}
            if let parent=values["parent"] as? String {values["parent"]=try boneIndex(parent,in:project)}
            var object=try JSONSerialization.jsonObject(with:JSONEncoder().encode(project.bones[i])) as! [String:Any]
            for (key,value) in values {if key=="parent",value is NSNull {object.removeValue(forKey:key)} else {object[key]=value}}
            project.bones[i]=try JSONDecoder().decode(Bone.self,from:JSONSerialization.data(withJSONObject:object))
        case "add_bone":
            let parent=try boneIndex(request["bone"],in:project)
            let id=request["bone_id"] as? String ?? UUID().uuidString.lowercased()
            project.bones.append(Bone(id:id,name:request["name"] as? String ?? "New bone",parent:parent,x:0,y:project.bones[parent].length,length:50,angle:0,width:20,layer:10,color:[0.5,0.7,0.9]))
            for i in project.frames.indices {project.frames[i].angles.append(0)}
        case "delete_bone":
            let i=try boneIndex(request["bone"],in:project)
            if let supplied=request["include_descendants"] {
                guard let value=supplied as? NSNumber,CFGetTypeID(value)==CFBooleanGetTypeID() else {
                    throw RigError(code:"invalid_request",message:"include_descendants must be a boolean")
                }
            }
            let removed=subtree(i,in:project)
            guard removed.count == 1 || request["include_descendants"] as? Bool == true else {
                throw RigError(code:"bone_has_children",message:"Bone has children; use include_descendants:true to delete its subtree")
            }
            let remaining=project.bones.indices.filter{!removed.contains($0)}
            guard !remaining.isEmpty else {throw RigError(code:"invalid_request",message:"Cannot delete every bone; keep at least one root")}
            let remap=Dictionary(uniqueKeysWithValues:remaining.enumerated().map{($0.element,$0.offset)})
            project.bones=remaining.map { old in
                var bone=project.bones[old];bone.parent=bone.parent.flatMap{remap[$0]};return bone
            }
            for f in project.frames.indices {project.frames[f].angles=remaining.map{project.frames[f].angles[$0]}}
        case "import_image", "replace_image":
            let i=try boneIndex(request["bone"],in:project)
            guard let path=request["image"] as? String else {throw RigError(code:"invalid_request",message:"image path required")}
            let (data,size)=try image(path)
            project.bones[i].image=data
            if command == "import_image" {project.bones[i].width=project.bones[i].length*size.width/size.height}
        case "keyframe":
            let time=try number(request["time"],label:"time")
            guard time>=0,time<=project.duration else {throw RigError(code:"invalid_request",message:"time must be within project duration")}
            guard !(request["angles"] != nil && request["pose"] != nil) else {throw RigError(code:"invalid_request",message:"Use angles or pose, not both")}
            var angles=project.bones.map(\.angle)
            if let supplied=request["angles"] {
                guard let list=supplied as? [Any] else {throw RigError(code:"invalid_request",message:"angles array required")}
                guard list.count == project.bones.count else {throw RigError(code:"validation_failed",message:"Keyframe must have one angle per bone")}
                angles=try list.map{try number($0,label:"angle")}
            }
            if let supplied=request["pose"] {
                guard let pose=supplied as? [String:Any] else {throw RigError(code:"invalid_request",message:"pose object required")}
                for (id,value) in pose {angles[try boneIndex(id,in:project)]=try number(value,label:"pose.\(id)")}
            }
            project.frames.removeAll{abs($0.time-time)<0.025};project.frames.append(Frame(time:time,angles:angles,label:request["label"] as? String));project.frames.sort{$0.time<$1.time}
        default: break
        }
    }
}
