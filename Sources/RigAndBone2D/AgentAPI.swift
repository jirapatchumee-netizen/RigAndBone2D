import AppKit

/// JSONL v1 remains backwards compatible; recipe and transaction features are additive.
enum AgentAPI {
    static var commands: [String] { ["capabilities","get_schema","new","inspect","validate","sample","render","export_sheet","apply_recipe","batch"] + ProjectCommands.mutations.sorted() }
    static func run() {
        while let line=readLine() {
            var response:[String:Any];var id:Any=NSNull()
            do {
                let parsed: Any
                do {parsed=try JSONSerialization.jsonObject(with:Data(line.utf8))}
                catch {throw RigError(code:"invalid_json",message:"Request is not valid JSON")}
                guard let request=parsed as? [String:Any] else {throw RigError(code:"invalid_request",message:"Expected a JSON object")}
                id=request["id"] ?? NSNull();response=["ok":true,"result":try execute(request)]
            } catch let error as RigError {
                response=["ok":false,"error":error.message,"error_code":error.code]
                if let context=error.context {response["context"]=context}
            } catch let error as DecodingError {
                response=["ok":false,"error":String(describing:error),"error_code":"invalid_schema"]
            } catch {response=["ok":false,"error":error.localizedDescription,"error_code":"io_error"]}
            response["id"]=id
            if let data=try? JSONSerialization.data(withJSONObject:response,options:[.sortedKeys]),let text=String(data:data,encoding:.utf8) {print(text);fflush(stdout)}
        }
    }
    static func summary(_ project:Project) -> [String:Any] {
        ["bones":project.bones.count,"keyframes":project.frames.count,"duration":project.duration,"boneIDs":project.bones.enumerated().map{$0.element.id ?? "bone-\($0.offset)"},"assets":project.bones.filter{$0.image != nil}.count]
    }
    static func execute(_ r:[String:Any]) throws -> [String:Any] {
        guard let command=r["command"] as? String,commands.contains(command) else {throw RigError(code:"unknown_command",message:"Unknown command. Use capabilities.")}
        for key in ["dry_run","replace","overwrite"] {
            if let supplied=r[key] {
                guard let value=supplied as? NSNumber,CFGetTypeID(value)==CFBooleanGetTypeID() else {throw RigError(code:"invalid_request",message:"\(key) must be a boolean")}
            }
        }
        if let value=r["expected_revision"],!(value is String) {throw RigError(code:"invalid_request",message:"expected_revision must be a string")}
        if command=="capabilities" {return ["protocolVersion":1,"recipeVersion":1,"commands":commands,"projectVersion":1,"units":"pixels, degrees, seconds; y down","boneSelector":"integer index or stable ID","parentRule":"stored parent index must precede child; recipe order is arbitrary","meshDeformation":false,"assetReplacement":true,"imageOffsets":true,"layerReordering":true,"transactions":true,"dryRun":true,"writerLock":true]}
        if command=="get_schema" {return RecipeCompiler.schema}
        guard let path=r["project"] as? String,!path.isEmpty else {throw RigError(code:"invalid_request",message:"project path is required")}
        let url=URL(fileURLWithPath:path),exists=FileManager.default.fileExists(atPath:url.path)
        let expected=r["expected_revision"] as? String,dryRun=r["dry_run"] as? Bool ?? false
        if command=="new" {
            let preset=r["preset"] as? String ?? "demo"
            guard ["demo","empty"].contains(preset) else {throw RigError(code:"invalid_request",message:"preset must be demo or empty")}
            if exists && r["overwrite"] as? Bool != true {throw RigError(code:"already_exists",message:"Project exists; use overwrite:true explicitly")}
            let project=preset=="empty" ? Project(bones:[Bone(id:"root",visible:false,name:"Root",parent:nil,x:0,y:0,length:1,angle:0,width:1,layer:0,color:[0,0,0])],frames:[]) : demo()
            var result=summary(project);result["project"]=url.path;result["dryRun"]=dryRun
            if !dryRun {result["revision"]=try ProjectStore.save(project,to:url,expectedRevision:expected,createOnly:r["overwrite"] as? Bool != true)}
            return result
        }
        if command=="apply_recipe" {
            guard let path=r["recipe"] as? String else {throw RigError(code:"invalid_request",message:"recipe path is required")}
            if exists {
                guard r["replace"] as? Bool == true,let expected else {throw RigError(code:"replacement_required",message:"Replacing a project requires replace:true and expected_revision")}
                guard try ProjectStore.revision(Data(contentsOf:url))==expected else {throw RigError(code:"revision_conflict",message:"Project changed; inspect again")}
            }
            let project=try RecipeCompiler.compile(url:URL(fileURLWithPath:path))
            var result=summary(project);result["project"]=url.path;result["dryRun"]=dryRun
            if !dryRun {result["revision"]=try ProjectStore.save(project,to:url,expectedRevision:expected,createOnly:!exists)}
            return result
        }
        let snapshot=try ProjectStore.load(url);var project=snapshot.project
        if let expected,expected != snapshot.revision {throw RigError(code:"revision_conflict",message:"Project changed; inspect again")}
        switch command {
        case "inspect":
            var object=try JSONSerialization.jsonObject(with:JSONEncoder().encode(project)) as! [String:Any]
            var bones=object["bones"] as! [[String:Any]]
            for i in bones.indices {bones[i]["imageBytes"]=project.bones[i].image?.count ?? 0;bones[i].removeValue(forKey:"image");bones[i]["index"]=i}
            object["bones"]=bones;object["revision"]=snapshot.revision
            let transforms=Stage().transforms(project)
            object["worldBones"]=project.bones.indices.map { i -> [String:Any] in
                let t=transforms[i],a=t.transform(NSPoint.zero),b=t.transform(NSPoint(x:0,y:project.bones[i].length))
                return ["index":i,"id":project.bones[i].id!,"origin":[a.x,a.y],"end":[b.x,b.y]]
            }
            return object
        case "validate":var result=summary(project);result["valid"]=true;result["revision"]=snapshot.revision;return result
        case "sample":
            let time=try ProjectCommands.number(r["time"],label:"time")
            guard time>=0,time<=project.duration else {throw RigError(code:"invalid_request",message:"time must be within project duration")}
            ProjectCore.sample(&project,time:time)
            return ["time":time,"angles":project.bones.map(\.angle),"pose":Dictionary(uniqueKeysWithValues:project.bones.map{($0.id!,$0.angle)}),"revision":snapshot.revision]
        case "render","export_sheet":
            guard let output=r["output"] as? String,!output.isEmpty else {throw RigError(code:"invalid_request",message:"output path required")}
            if let supplied=r["time"] {let time=try ProjectCommands.number(supplied,label:"time");guard time>=0,time<=project.duration else {throw RigError(code:"invalid_request",message:"Invalid time")};ProjectCore.sample(&project,time:time)}
            let outputURL=URL(fileURLWithPath:output)
            guard outputURL.resolvingSymlinksInPath().standardizedFileURL != url.resolvingSymlinksInPath().standardizedFileURL else {throw RigError(code:"invalid_request",message:"Render output cannot replace the project")}
            try ProjectCore.render(project,to:outputURL,sheet:command=="export_sheet")
            return ["output":outputURL.path,"frames":command=="export_sheet" ? 24 : 1,"cellWidth":384,"cellHeight":384,"columns":command=="export_sheet" ? 6 : 1,"duration":project.duration,"revision":snapshot.revision]
        case "batch":
            guard let operations=r["operations"] as? [[String:Any]],!operations.isEmpty,operations.count<=1024 else {throw RigError(code:"invalid_request",message:"operations must contain 1–1024 mutation objects")}
            for (i,operation) in operations.enumerated() {
                guard Set(operation.keys).isDisjoint(with:["project","expected_revision","dry_run"]) else {throw RigError(code:"invalid_request",message:"Batch targets one project; revision and dry_run belong on the outer request",context:"operations[\(i)]")}
                do {try ProjectCommands.apply(operation,to:&project)}
                catch let error as RigError {throw RigError(code:error.code,message:error.message,context:"operations[\(i)]" + (error.context.map{".\($0)"} ?? ""))}
            }
        default:try ProjectCommands.apply(r,to:&project)
        }
        try ProjectCore.validate(project)
        var result=summary(project);result["project"]=url.path;result["dryRun"]=dryRun
        result["revision"]=dryRun ? snapshot.revision : try ProjectStore.save(project,to:url,expectedRevision:snapshot.revision)
        return result
    }
}
