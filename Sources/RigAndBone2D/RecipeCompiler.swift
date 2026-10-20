import AppKit

struct RigRecipe: Decodable {
    let schemaVersion: Int
    let name: String?
    let duration: Double
    let bones: [RecipeBone]
    let frames: [RecipeFrame]
}
struct RecipeBone: Decodable {
    let id: String
    let name: String?
    let parent: String?
    let image: String?
    let visible: Bool?
    let x: Double?; let y: Double?; let length: Double?; let width: Double?; let angle: Double?
    let imageOffsetX: Double?; let imageOffsetY: Double?
    let layer: Int?; let color: [Double]?; let pivotX: Double?; let pivotY: Double?
}
struct RecipeFrame: Decodable { let time: Double; let label: String?; let pose: [String:Double] }

enum RecipeCompiler {
    static let idPattern = "^[A-Za-z][A-Za-z0-9_.-]{0,63}$"
    static var schema: [String:Any] {
        var properties: [String:Any] = [:]
        for key in ["x","y","angle","imageOffsetX","imageOffsetY"] {properties[key]=["type":["number","null"]]}
        for key in ["length","width"] {properties[key]=["type":["number","null"],"exclusiveMinimum":0]}
        for key in ["pivotX","pivotY"] {properties[key]=["type":["number","null"],"minimum":0,"maximum":1]}
        properties["id"]=["type":"string","pattern":idPattern]
        properties["name"]=["type":["string","null"]]
        properties["parent"]=["type":["string","null"]]
        properties["image"]=["type":["string","null"],"minLength":1]
        properties["visible"]=["type":["boolean","null"]]
        properties["layer"]=["type":["integer","null"]]
        properties["color"]=["type":["array","null"],"minItems":3,"maxItems":3,"items":["type":"number","minimum":0,"maximum":1]]
        return ["$schema":"https://json-schema.org/draft/2020-12/schema","title":"RigAndBone2D recipe v1","type":"object","additionalProperties":false,
                "required":["schemaVersion","duration","bones","frames"],
                "properties":["schemaVersion":["const":1],"name":["type":["string","null"]],"duration":["type":"number","exclusiveMinimum":0,"maximum":120],
                              "bones":["type":"array","minItems":1,"maxItems":512,"items":["type":"object","required":["id"],"additionalProperties":false,"properties":properties]],
                              "frames":["type":"array","maxItems":10000,"items":["type":"object","required":["time","pose"],"additionalProperties":false,
                                    "properties":["time":["type":"number","minimum":0],"label":["type":["string","null"]],"pose":["type":"object","additionalProperties":["type":"number"]]]]]]]
    }
    static func compile(url: URL) throws -> Project {
        let data=try Data(contentsOf:url)
        // Codable ignores unknown keys; catch misspellings before compiling a valid but wrong rig.
        guard let object=try JSONSerialization.jsonObject(with:data) as? [String:Any] else {throw RigError(code:"invalid_recipe",message:"Recipe must be a JSON object")}
        func checkKeys(_ value:[String:Any],allowed:Set<String>,path:String)throws {
            let unknown=Set(value.keys).subtracting(allowed)
            if !unknown.isEmpty {throw RigError(code:"invalid_recipe",message:"Unknown fields: \(unknown.sorted().joined(separator:", "))",context:path)}
        }
        try checkKeys(object,allowed:["schemaVersion","name","duration","bones","frames"],path:"recipe")
        let boneFields=Set((schema["properties"] as! [String:Any])["bones"].flatMap { $0 as? [String:Any] }?["items"].flatMap { $0 as? [String:Any] }?["properties"].flatMap { $0 as? [String:Any] }?.keys.map{$0} ?? [])
        for (i,bone) in (object["bones"] as? [[String:Any]] ?? []).enumerated() {try checkKeys(bone,allowed:boneFields,path:"bones[\(i)]")}
        for (i,frame) in (object["frames"] as? [[String:Any]] ?? []).enumerated() {try checkKeys(frame,allowed:["time","label","pose"],path:"frames[\(i)]")}
        let recipe=try JSONDecoder().decode(RigRecipe.self,from:data)
        guard recipe.schemaVersion==1,!recipe.bones.isEmpty,recipe.bones.count<=512,recipe.frames.count<=10000 else {
            throw RigError(code:"invalid_recipe",message:"Unsupported recipe version or size")
        }
        var byID:[String:RecipeBone]=[:]
        for bone in recipe.bones {
            guard bone.id.range(of:idPattern,options:.regularExpression) != nil else {throw RigError(code:"invalid_recipe",message:"Invalid bone ID",context:bone.id)}
            guard byID[bone.id]==nil else {throw RigError(code:"duplicate_id",message:"Duplicate bone ID",context:bone.id)}
            byID[bone.id]=bone
        }
        var visiting=Set<String>(),visited=Set<String>(),ordered:[RecipeBone]=[]
        func visit(_ id:String)throws {
            if visited.contains(id) {return}
            guard let bone=byID[id] else {throw RigError(code:"unknown_bone",message:"Parent ID does not exist",context:id)}
            guard !visiting.contains(id) else {throw RigError(code:"hierarchy_cycle",message:"Bone hierarchy contains a cycle",context:id)}
            visiting.insert(id)
            if let parent=bone.parent {try visit(parent)}
            visiting.remove(id);visited.insert(id);ordered.append(bone)
        }
        for bone in recipe.bones {try visit(bone.id)}
        var indices:[String:Int]=[:],bones:[Bone]=[]
        for b in ordered {
            let length=b.length ?? 50
            var bone=Bone(id:b.id,visible:b.visible,name:b.name ?? b.id,parent:b.parent.flatMap{indices[$0]},x:b.x ?? 0,y:b.y ?? 0,length:length,angle:b.angle ?? 0,width:b.width ?? 20,layer:b.layer ?? 0,color:b.color ?? [0.5,0.7,0.9],pivotX:b.pivotX ?? 0.5,pivotY:b.pivotY ?? 0.15,imageOffsetX:b.imageOffsetX,imageOffsetY:b.imageOffsetY)
            if let image=b.image {
                let imageURL=URL(fileURLWithPath:image,relativeTo:url.deletingLastPathComponent()).standardizedFileURL
                let (data,size)=try ProjectCommands.image(imageURL.path)
                bone.image=data
                if b.width==nil {bone.width=length*size.width/size.height}
            }
            indices[b.id]=bones.count;bones.append(bone)
        }
        let rest=bones.map(\.angle)
        let frames=try recipe.frames.enumerated().map { offset,frame -> Frame in
            var angles=rest
            for (id,angle) in frame.pose {
                guard let index=indices[id] else {throw RigError(code:"unknown_bone",message:"Pose references an unknown bone",context:"frames[\(offset)].pose.\(id)")}
                angles[index]=angle
            }
            return Frame(time:frame.time,angles:angles,label:frame.label)
        }.sorted{$0.time<$1.time}
        let project=Project(name:recipe.name,bones:bones,frames:frames,duration:recipe.duration)
        try ProjectCore.validate(project)
        return project
    }
}
