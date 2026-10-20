import AppKit
import UniformTypeIdentifiers
class RigWindow: NSWindow {
    let history=UndoManager()
    override var undoManager:UndoManager? {history}
    @objc func undo(_ sender:Any?) {history.undo()}
    @objc func redo(_ sender:Any?) {history.redo()}
    override func validateMenuItem(_ menuItem:NSMenuItem)->Bool {
        if menuItem.action == #selector(undo(_:)) {menuItem.title=history.undoMenuItemTitle;return history.canUndo}
        if menuItem.action == #selector(redo(_:)) {menuItem.title=history.redoMenuItemTitle;return history.canRedo}
        return super.validateMenuItem(menuItem)
    }
}
class RigFieldEditor: NSTextView {
    let textHistory=UndoManager()
    override var undoManager:UndoManager? {textHistory}
}
class PropertySlider: NSSlider {
    var beginGesture:(()->Void)?
    var endGesture:(()->Void)?
    override func mouseDown(with event:NSEvent) {
        beginGesture?()
        defer {endGesture?()}
        super.mouseDown(with:event)
    }
}
struct EditorSnapshot {
    var project:Project
    var selected:Int
    var time:Double
}
class Editor: NSObject, NSApplicationDelegate, NSWindowDelegate, NSTableViewDataSource, NSTableViewDelegate {
    var project=demo(), selected=1, zoom:CGFloat=1.8, showBones=true
    var window:NSWindow!,stage=Stage(),table=NSTableView(), inspector=NSStackView(),status=NSTextField(labelWithString:"")
    var timeSlider=NSSlider(value:0,minValue:0,maxValue:2,target:nil,action:nil),timer:Timer?,time=0.0
    var fields:[String:NSTextField]=[:]
    var propertySliders:[String:PropertySlider]=[:]
    var sliderEdit:EditorSnapshot?
    let sliderRanges:[String:ClosedRange<Double>]=["X":-300...300,"Y":-300...300,"Length":1...300,"Width":1...200,"Angle":-180...180,"Pivot X":0...1,"Pivot Y":0...1,"Image X":-300...300,"Image Y":-300...300]
    func commitFields() {window?.makeFirstResponder(stage)}
    func beginSliderEdit() {commitFields();stop();sliderEdit=snapshot()}
    func finishSliderEdit(_ key:String) {if let before=sliderEdit {record(before,"Change "+key)};sliderEdit=nil;refreshFields()}
    @objc func sliderChanged(_ sender:PropertySlider) {
        guard let key=sender.identifier?.rawValue else{return}
        stop();let before=snapshot()
        applyProperty(key,value:sender.doubleValue)
        if sliderEdit == nil {record(before,"Change "+key)}
        refresh()
    }
    func applyProperty(_ key:String,value:Double) {
        switch key {
        case "X":project.bones[selected].x=value
        case "Y":project.bones[selected].y=value
        case "Image X":project.bones[selected].imageOffsetX=value
        case "Image Y":project.bones[selected].imageOffsetY=value
        case "Length":project.bones[selected].length=value
        case "Width":project.bones[selected].width=value
        case "Angle":project.bones[selected].angle=value
        case "Pivot X":project.bones[selected].pivotX=max(0,min(1,value))
        case "Pivot Y":project.bones[selected].pivotY=max(0,min(1,value))
        default:break
        }
    }
    var sidebarHint=NSTextField(labelWithString:"Drag up = front · Drag down = back")
    var sidebarBones:[Int]=[]
    var refreshingSidebar=false
    static let layerDragType=NSPasteboard.PasteboardType("local.frostnova.rigandbone2d.layer")
    var layerDrag:(token:String,index:Int,order:[Int])?
    var moveImageMode=false
    var moveImageButton=NSButton()
    let fieldEditor=RigFieldEditor()
    var canvasEdit:EditorSnapshot?
    var history:UndoManager {window.undoManager!}
    func snapshot()->EditorSnapshot {EditorSnapshot(project:project,selected:selected,time:time)}
    func record(_ before:EditorSnapshot,_ name:String) {
        guard before.project != project else{return}
        history.beginUndoGrouping()
        history.registerUndo(withTarget:self) {$0.restore(before,name)}
        history.setActionName(name)
        history.endUndoGrouping()
    }
    func restore(_ state:EditorSnapshot,_ name:String) {
        let current=snapshot()
        stop();canvasEdit=nil;sliderEdit=nil;stage.cancelDrag();layerDrag=nil
        project=state.project;selected=max(0,min(state.selected,project.bones.count-1));time=max(0,min(state.time,project.duration))
        history.registerUndo(withTarget:self) {$0.restore(current,name)}
        history.setActionName(name);refresh()
    }
    func beginCanvasEdit() {canvasEdit=snapshot()}
    func finishCanvasEdit() {
        if let before=canvasEdit {record(before,moveImageMode ? "Move Image" : "Move Bone")}
        canvasEdit=nil
    }
    func clearHistory() {canvasEdit=nil;sliderEdit=nil;stage.cancelDrag();history.removeAllActions();fieldEditor.textHistory.removeAllActions()}
    func windowWillReturnFieldEditor(_ sender:NSWindow,to client:Any?)->Any? {fieldEditor.textHistory.removeAllActions();return fieldEditor}
    var loadedURL: URL?
    var loadedRevision: String?
    func applicationDidFinishLaunching(_ notification:Notification) {
        let menu=NSMenu();let appItem=NSMenuItem();menu.addItem(appItem);let appMenu=NSMenu();appItem.submenu=appMenu
        appMenu.addItem(withTitle:"Quit RigAndBone2D",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q");NSApp.mainMenu=menu
        let editItem=NSMenuItem();menu.addItem(editItem);let editMenu=NSMenu(title:"Edit");editItem.submenu=editMenu
        editMenu.addItem(withTitle:"Undo",action:#selector(RigWindow.undo(_:)),keyEquivalent:"z")
        let redoItem=editMenu.addItem(withTitle:"Redo",action:#selector(RigWindow.redo(_:)),keyEquivalent:"Z");redoItem.keyEquivalentModifierMask=[.command,.shift]
        editMenu.addItem(.separator())
        editMenu.addItem(withTitle:"Cut",action:#selector(NSText.cut(_:)),keyEquivalent:"x")
        editMenu.addItem(withTitle:"Copy",action:#selector(NSText.copy(_:)),keyEquivalent:"c")
        editMenu.addItem(withTitle:"Paste",action:#selector(NSText.paste(_:)),keyEquivalent:"v")
        editMenu.addItem(withTitle:"Select All",action:#selector(NSText.selectAll(_:)),keyEquivalent:"a")
        window=RigWindow(contentRect:NSRect(x:0,y:0,width:1280,height:820),styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
        window.delegate=self;history.levelsOfUndo=100;history.groupsByEvent=false;fieldEditor.isFieldEditor=true;fieldEditor.allowsUndo=true
        window.title="RigAndBone2D — Character Animation Studio";window.minSize=NSSize(width:1000,height:700);window.center()
        let root=NSView();root.translatesAutoresizingMaskIntoConstraints=false
        window.contentView!.addSubview(root);NSLayoutConstraint.activate([root.leadingAnchor.constraint(equalTo:window.contentView!.leadingAnchor),root.trailingAnchor.constraint(equalTo:window.contentView!.trailingAnchor),root.topAnchor.constraint(equalTo:window.contentView!.topAnchor),root.bottomAnchor.constraint(equalTo:window.contentView!.bottomAnchor)])
        let toolbar=NSStackView();toolbar.edgeInsets=NSEdgeInsets(top:12,left:12,bottom:12,right:12);toolbar.spacing=8
        for (title,action) in [("New",#selector(newProject)),("Open…",#selector(openProject)),("Save…",#selector(saveProject)),("Import PNG…",#selector(importImage)),("Add bone",#selector(addBone)),("Export sheet…",#selector(exportSheet)),("Bones",#selector(toggleBones)),("−",#selector(zoomOut)),("+",#selector(zoomIn)),("Fit",#selector(fitView))] {toolbar.addArrangedSubview(button(title,action))}
        root.addSubview(toolbar);toolbar.widthAnchor.constraint(equalTo:root.widthAnchor).isActive=true
        let middle=NSStackView();middle.spacing=0;middle.alignment = .top
        let left=NSStackView();left.orientation = .vertical;left.edgeInsets=NSEdgeInsets(top:14,left:12,bottom:14,right:12)
        left.addArrangedSubview(NSTextField(labelWithString:"PARTS"))
        sidebarHint.font = .systemFont(ofSize:11);sidebarHint.textColor = .secondaryLabelColor;left.addArrangedSubview(sidebarHint)
        let column=NSTableColumn(identifier:NSUserInterfaceItemIdentifier("name"));column.title="Bone";table.addTableColumn(column);table.headerView=nil;table.delegate=self;table.dataSource=self;table.rowHeight=30
        table.registerForDraggedTypes([Self.layerDragType]);table.setDraggingSourceOperationMask(.move,forLocal:true)
        let scroll=NSScrollView();scroll.documentView=table;scroll.hasVerticalScroller=true;left.addArrangedSubview(scroll);left.widthAnchor.constraint(equalToConstant:230).isActive=true
        stage.owner=self;stage.translatesAutoresizingMaskIntoConstraints=false
        inspector.orientation = .vertical;inspector.alignment = .leading;inspector.edgeInsets=NSEdgeInsets(top:14,left:14,bottom:14,right:14);inspector.widthAnchor.constraint(equalToConstant:280).isActive=true
        inspector.addArrangedSubview(NSTextField(labelWithString:"BONE PROPERTIES"))
        for key in ["Name","Parent","X","Y","Length","Width","Angle","Pivot X","Pivot Y","Image X","Image Y"] {
            let row=NSStackView();let label=NSTextField(labelWithString:key);label.widthAnchor.constraint(equalToConstant:65).isActive=true
            let field=NSTextField();field.identifier=NSUserInterfaceItemIdentifier(key);field.cell?.sendsActionOnEndEditing=true;field.target=self;field.action=#selector(propertyChanged(_:));field.widthAnchor.constraint(equalToConstant:160).isActive=true;fields[key]=field;row.addArrangedSubview(label);row.addArrangedSubview(field);inspector.addArrangedSubview(row)
            if let range=sliderRanges[key] {
                let slider=PropertySlider(value:0,minValue:range.lowerBound,maxValue:range.upperBound,target:self,action:#selector(sliderChanged(_:)))
                slider.identifier=NSUserInterfaceItemIdentifier(key);slider.isContinuous=true
                slider.widthAnchor.constraint(equalToConstant:236).isActive=true
                slider.toolTip="Adjust "+key+" · Command-Z to undo"
                slider.beginGesture={ [weak self] in self?.beginSliderEdit() }
                slider.endGesture={ [weak self] in self?.finishSliderEdit(key) }
                propertySliders[key]=slider;inspector.addArrangedSubview(slider)
            }
        }
        moveImageButton=NSButton(checkboxWithTitle:"Move image",target:self,action:#selector(toggleMoveImage))
        inspector.addArrangedSubview(moveImageButton)
        inspector.addArrangedSubview(button("Reset image position",#selector(resetImagePosition)))
        inspector.addArrangedSubview(button("Replace PNG…",#selector(replaceImage)))
        inspector.addArrangedSubview(button("Add child bone",#selector(addBone)))
        inspector.addArrangedSubview(button("Delete bone…",#selector(deleteBone)))
        let hint=NSTextField(wrappingLabelWithString:"Drag X/Y arrows to move the rig attachment. Drag the square to move freely.\nParent: bone index, or -1 for root.\nPivot: normalized image coordinates.\nImage X/Y: offset in local bone pixels.\nMove image: drag artwork to overlap joints.\nImport PNG fits artwork aspect ratio.\nReplace PNG keeps size, pivot and animation. Align new artwork on the same canvas.\nSelect a bone, adjust a pose, then add a keyframe.");hint.font = .systemFont(ofSize:11);hint.textColor = .secondaryLabelColor;hint.widthAnchor.constraint(equalToConstant:242).isActive=true;inspector.addArrangedSubview(hint)
        let inspectorScroll=NSScrollView();inspectorScroll.hasVerticalScroller=true;inspectorScroll.drawsBackground=false
        inspectorScroll.documentView=inspector;inspectorScroll.widthAnchor.constraint(equalToConstant:280).isActive=true
        inspector.translatesAutoresizingMaskIntoConstraints=false
        NSLayoutConstraint.activate([inspector.topAnchor.constraint(equalTo:inspectorScroll.contentView.topAnchor),inspector.leadingAnchor.constraint(equalTo:inspectorScroll.contentView.leadingAnchor)])
        middle.addArrangedSubview(left);middle.addArrangedSubview(stage);middle.addArrangedSubview(inspectorScroll);root.addSubview(middle);middle.widthAnchor.constraint(equalTo:root.widthAnchor).isActive=true;stage.widthAnchor.constraint(greaterThanOrEqualToConstant:400).isActive=true
        for v in [left,stage,inspectorScroll] {v.heightAnchor.constraint(equalTo:middle.heightAnchor).isActive=true}
        let timeline=NSStackView();timeline.edgeInsets=NSEdgeInsets(top:12,left:14,bottom:12,right:14)
        timeline.addArrangedSubview(button("Play / Pause",#selector(play)));timeline.addArrangedSubview(button("Add keyframe",#selector(addKey)));timeline.addArrangedSubview(button("Delete keyframe",#selector(deleteKey)))
        timeSlider.target=self;timeSlider.action=#selector(scrub);timeSlider.isContinuous=true;timeline.addArrangedSubview(timeSlider);root.addSubview(timeline);timeline.widthAnchor.constraint(equalTo:root.widthAnchor).isActive=true
        root.addSubview(status)
        for view in [toolbar,middle,timeline,status] {view.translatesAutoresizingMaskIntoConstraints=false}
        NSLayoutConstraint.activate([
            toolbar.topAnchor.constraint(equalTo:root.topAnchor),toolbar.leadingAnchor.constraint(equalTo:root.leadingAnchor),toolbar.heightAnchor.constraint(equalToConstant:54),
            middle.topAnchor.constraint(equalTo:toolbar.bottomAnchor),middle.leadingAnchor.constraint(equalTo:root.leadingAnchor),middle.bottomAnchor.constraint(equalTo:timeline.topAnchor),
            timeline.leadingAnchor.constraint(equalTo:root.leadingAnchor),timeline.bottomAnchor.constraint(equalTo:status.topAnchor),timeline.heightAnchor.constraint(equalToConstant:52),
            status.leadingAnchor.constraint(equalTo:root.leadingAnchor,constant:14),status.trailingAnchor.constraint(equalTo:root.trailingAnchor,constant:-14),status.bottomAnchor.constraint(equalTo:root.bottomAnchor),status.heightAnchor.constraint(equalToConstant:28)
        ])
        window.makeKeyAndOrderFront(nil);NSApp.activate(ignoringOtherApps:true);refresh()
        if let index=CommandLine.arguments.firstIndex(of:"--project"),index+1<CommandLine.arguments.count {
            loadProject(at:URL(fileURLWithPath:CommandLine.arguments[index+1]))
        }
        if CommandLine.arguments.contains("--play") {showBones=false;play()}
    }
    func button(_ title:String,_ action:Selector)->NSButton {let b=NSButton(title:title,target:self,action:action);b.bezelStyle = .rounded;return b}
    func numberOfRows(in tableView:NSTableView)->Int {sidebarBones.count}
    func tableView(_ tableView:NSTableView,viewFor tableColumn:NSTableColumn?,row:Int)->NSView? {
        guard sidebarBones.indices.contains(row) else{return nil}
        let index=sidebarBones[row],bone=project.bones[index]
        let tag=bone.visible == false ? " [hidden]" : bone.image == nil ? " [shape]" : ""
        return NSTextField(labelWithString:bone.name+tag)
    }
    func tableViewSelectionDidChange(_ notification:Notification) {
        guard !refreshingSidebar,sidebarBones.indices.contains(table.selectedRow) else{return}
        let next=sidebarBones[table.selectedRow]
        commitFields();selected=next;refresh()
    }
    func tableView(_ tableView:NSTableView,pasteboardWriterForRow row:Int)->NSPasteboardWriting? {
        guard sidebarBones.indices.contains(row) else{return nil}
        commitFields();stop()
        let token=UUID().uuidString
        layerDrag=(token,sidebarBones[row],sidebarBones)
        let item=NSPasteboardItem();item.setString(token,forType:Self.layerDragType);return item
    }
    func validLayerDrag(_ info:NSDraggingInfo)->Bool {
        guard let source=info.draggingSource as? NSTableView,source === table,
              let drag=layerDrag,info.draggingPasteboard.string(forType:Self.layerDragType) == drag.token else{return false}
        return drag.order == Array(ProjectCore.drawOrder(project).reversed())
    }
    func tableView(_ tableView:NSTableView,validateDrop info:NSDraggingInfo,proposedRow row:Int,proposedDropOperation operation:NSTableView.DropOperation)->NSDragOperation {
        guard (0...sidebarBones.count).contains(row),validLayerDrag(info) else{return []}
        tableView.setDropRow(row,dropOperation:.above)
        return .move
    }
    func tableView(_ tableView:NSTableView,acceptDrop info:NSDraggingInfo,row:Int,dropOperation operation:NSTableView.DropOperation)->Bool {
        guard operation == .above,(0...sidebarBones.count).contains(row),validLayerDrag(info),let drag=layerDrag,
              let sourceRow=drag.order.firstIndex(of:drag.index) else{return false}
        var order=drag.order;order.remove(at:sourceRow);order.insert(drag.index,at:row > sourceRow ? row-1 : row)
        layerDrag=nil
        guard order != drag.order else{return true}
        let before=snapshot()
        do {
            try ProjectCommands.apply(["command":"reorder_layers","order":order],to:&project)
            record(before,"Reorder Layers");refresh();return true
        } catch {alert(error.localizedDescription);return false}
    }
    func refreshFields() {
        guard project.bones.indices.contains(selected) else{return};let b=project.bones[selected]
        fields["Name"]?.stringValue=b.name
        for (k,v) in [("Parent",Double(b.parent ?? -1)),("X",b.x),("Y",b.y),("Length",b.length),("Width",b.width),("Angle",b.angle),("Pivot X",b.pivotX),("Pivot Y",b.pivotY),("Image X",b.imageOffsetX ?? 0),("Image Y",b.imageOffsetY ?? 0)] {
            fields[k]?.stringValue=String(format:"%.2f",v)
            if let slider=propertySliders[k],let range=sliderRanges[k] {
                if sliderEdit == nil {slider.minValue=min(range.lowerBound,v);slider.maxValue=max(range.upperBound,v)}
                slider.doubleValue=v
            }
        }
    }
    func refresh() {
        refreshingSidebar=true
        sidebarBones=Array(ProjectCore.drawOrder(project).reversed())
        table.reloadData()
        if let row=sidebarBones.firstIndex(of:selected) {table.selectRowIndexes(IndexSet(integer:row),byExtendingSelection:false)}
        refreshingSidebar=false;refreshFields();stage.needsDisplay=true;timeSlider.maxValue=project.duration;timeSlider.doubleValue=time;status.stringValue=String(format:"  %.2f s / %.2f s  ·  %d keyframes  ·  %d bones",time,project.duration,project.frames.count,project.bones.count)}
    @objc func propertyChanged(_ sender:NSTextField) {
        stop();guard let k=sender.identifier?.rawValue else{return}
        let parsed=Double(sender.stringValue.trimmingCharacters(in:.whitespacesAndNewlines))
        guard k == "Name" || parsed?.isFinite == true else {alert("Enter a finite number.");refresh();return}
        let v=parsed ?? 0
        if (k == "Length" || k == "Width") && v<=0 {alert("Size must be greater than zero.");refresh();return}
        if (k == "Pivot X" || k == "Pivot Y") && !(0...1).contains(v) {alert("Pivot must be between 0 and 1.");refresh();return}
        let before=snapshot()
        switch k {
        case "Name":project.bones[selected].name=sender.stringValue
        case "Parent":if let p=Int(exactly:v),p == -1 || (p>=0 && p<selected) {project.bones[selected].parent=p == -1 ? nil : p} else {alert("Parent must be an earlier bone index, or -1.")}
        default:applyProperty(k,value:v)
        };record(before,"Change "+k);refresh()
    }
    @objc func newProject(){commitFields();stop();layerDrag=nil;window.title="RigAndBone2D — Character Animation Studio";loadedURL=nil;loadedRevision=nil;project=demo();stage.pan = .zero;zoom=1.8;selected=1;time=0;clearHistory();refresh()}
    @objc func addBone(){commitFields();
        stop();layerDrag=nil
        let before=snapshot()
        do {try ProjectCommands.apply(["command":"add_bone","bone":selected],to:&project);selected=project.bones.count-1;record(before,"Add Bone");refresh()}
        catch {alert(error.localizedDescription)}
    }
    @objc func deleteBone(){commitFields();
        stop();layerDrag=nil;guard project.bones.indices.contains(selected) else{return}
        let descendants=ProjectCommands.subtree(selected,in:project).count-1
        let confirmation=NSAlert();confirmation.messageText="Delete \(project.bones[selected].name)?"
        confirmation.informativeText="This removes the selected bone, \(descendants) descendant bone(s), and their keyframe angles. You can undo this with Command-Z."
        confirmation.addButton(withTitle:"Cancel");confirmation.addButton(withTitle:"Delete")
        guard confirmation.runModal() == .alertSecondButtonReturn else{return}
        let before=snapshot()
        do {
            try ProjectCommands.apply(["command":"delete_bone","bone":selected,"include_descendants":true],to:&project)
            selected=min(selected,project.bones.count-1);record(before,"Delete Bone");refresh()
        } catch {alert(error.localizedDescription)}
    }
    @objc func toggleMoveImage(){commitFields();stop();moveImageMode=moveImageButton.state == .on;stage.cancelDrag();canvasEdit=nil;stage.needsDisplay=true}
    @objc func resetImagePosition(){commitFields();stop();guard project.bones.indices.contains(selected) else{return};let before=snapshot();project.bones[selected].imageOffsetX=nil;project.bones[selected].imageOffsetY=nil;record(before,"Reset Image Position");refresh()}
    @objc func toggleBones(){showBones.toggle();stage.needsDisplay=true}
    @objc func zoomIn(){stage.zoom(by:1.15,at:NSPoint(x:stage.bounds.midX,y:stage.bounds.midY))}
    @objc func zoomOut(){stage.zoom(by:1/1.15,at:NSPoint(x:stage.bounds.midX,y:stage.bounds.midY))}
    @objc func fitView(){stage.fitArtwork()}
    func stop(){timer?.invalidate();timer=nil}
    @objc func play(){commitFields();if timer != nil {stop();return};timer=Timer.scheduledTimer(withTimeInterval:1/60,repeats:true){[weak self] _ in guard let s=self else{return};s.time=(s.time+1/60).truncatingRemainder(dividingBy:s.project.duration);s.applyPose(s.time);s.refresh()}}
    func applyPose(_ t:Double){ProjectCore.sample(&project, time:t)}
    @objc func scrub(){commitFields();stop();time=timeSlider.doubleValue;applyPose(time);refresh()}
    @objc func addKey(){commitFields();stop();let before=snapshot();project.frames.removeAll{abs($0.time-time)<0.025};project.frames.append(Frame(time:time,angles:project.bones.map(\.angle)));record(before,"Add Keyframe");refresh()}
    @objc func deleteKey(){commitFields();stop();let before=snapshot();project.frames.removeAll{abs($0.time-time)<0.025};record(before,"Delete Keyframe");refresh()}
    func alert(_ text:String){let a=NSAlert();a.messageText=text;a.runModal()}
    @objc func saveProject(){commitFields();stop();let p=NSSavePanel();p.nameFieldStringValue="Character.rig2d";if p.runModal() == .OK,let url=p.url {do{let expected = loadedURL?.resolvingSymlinksInPath().standardizedFileURL == url.resolvingSymlinksInPath().standardizedFileURL ? loadedRevision : nil;loadedRevision=try ProjectStore.save(project,to:url,expectedRevision:expected);loadedURL=url}catch{alert(error.localizedDescription)}}}
    func loadProject(at url:URL) {commitFields();
        stop()
        do {
            let snapshot=try ProjectStore.load(url);let next=snapshot.project;loadedRevision=snapshot.revision;loadedURL=url
            layerDrag=nil;stage.pan = .zero;zoom=1.8;project=next;selected=min(1,next.bones.count-1);time=0;applyPose(0);clearHistory()
            window?.title="RigAndBone2D — \(next.name ?? url.deletingPathExtension().lastPathComponent)";refresh()
        } catch {alert(error.localizedDescription)}
    }
    func application(_ sender:NSApplication,openFiles filenames:[String]) {
        if let path=filenames.first {loadProject(at:URL(fileURLWithPath:path));window?.makeKeyAndOrderFront(nil)}
        sender.reply(toOpenOrPrint:.success)
    }
    @objc func openProject(){commitFields();let p=NSOpenPanel();p.allowsMultipleSelection=false;if p.runModal() == .OK,let url=p.url {loadProject(at:url)}}
    @objc func importImage(){chooseImage(command:"import_image")}
    @objc func replaceImage(){chooseImage(command:"replace_image")}
    func chooseImage(command:String){commitFields();
        stop();let p=NSOpenPanel();p.allowedContentTypes=[.png];p.allowsMultipleSelection=false
        p.message=command == "replace_image" ? "Replace selected bone artwork while keeping size, pivot and animation. Use the same canvas alignment." : "Import artwork and fit width to its aspect ratio."
        if p.runModal() == .OK,let url=p.url {
            let before=snapshot()
            do{try ProjectCommands.apply(["command":command,"bone":selected,"image":url.path],to:&project);record(before,command == "replace_image" ? "Replace Image" : "Import Image");refresh()}
            catch{alert(error.localizedDescription)}
        }
    }
    @objc func exportSheet(){commitFields();
        stop();let p=NSSavePanel();p.allowedContentTypes=[.png];p.nameFieldStringValue="Character-sheet.png";guard p.runModal() == .OK,let url=p.url else{return}
        do {
            try ProjectCore.render(project,to:url,sheet:true)
            let metadata="{\"columns\":6,\"rows\":4,\"frameWidth\":384,\"frameHeight\":384,\"frameCount\":24,\"duration\":\(project.duration)}"
            try metadata.write(to:url.deletingPathExtension().appendingPathExtension("json"),atomically:true,encoding:.utf8)
            status.stringValue="Exported 24 frames and JSON metadata."
        } catch {alert(error.localizedDescription)}
    }
}
