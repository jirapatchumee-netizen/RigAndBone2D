import AppKit
import UniformTypeIdentifiers

struct Bone: Codable, Equatable {
    var id: String? = nil
    var visible: Bool? = nil
    var name: String
    var parent: Int?
    var x: Double; var y: Double
    var length: Double; var angle: Double
    var width: Double; var layer: Int
    var color: [Double]
    var image: Data? = nil
    var pivotX: Double = 0.5; var pivotY: Double = 0.15
    var imageOffsetX: Double? = nil; var imageOffsetY: Double? = nil
    var imageRect: NSRect {
        NSRect(x:-width*pivotX+(imageOffsetX ?? 0),y:-length*pivotY+(imageOffsetY ?? 0),width:width,height:length)
    }
    mutating func moveImage(worldDelta: NSPoint, worldAngle: Double) {
        imageOffsetX = (imageOffsetX ?? 0)+worldDelta.x*cos(worldAngle)+worldDelta.y*sin(worldAngle)
        imageOffsetY = (imageOffsetY ?? 0)-worldDelta.x*sin(worldAngle)+worldDelta.y*cos(worldAngle)
    }
}
struct Frame: Codable, Equatable { var time: Double; var angles: [Double]; var label: String? = nil }
struct Project: Codable, Equatable { var version = 1; var name: String? = nil; var bones: [Bone]; var frames: [Frame]; var duration: Double = 2 }
func demo() -> Project {
    func b(_ name: String, _ parent: Int?, _ x: Double, _ y: Double, _ length: Double, _ angle: Double, _ width: Double, _ layer: Int, _ color: [Double]) -> Bone {
        Bone(name: name, parent: parent, x: x, y: y, length: length, angle: angle, width: width, layer: layer, color: color)
    }
    let blue = [0.25,0.43,0.65], skin = [0.96,0.74,0.46], brown = [0.40,0.26,0.19]
    let bones = [b("Root / Hip",nil,0,0,8,0,22,3,blue),b("Torso",0,0,0,85,180,64,4,blue),b("Head",1,0,85,58,0,68,8,skin),b("Back upper arm",1,-30,16,48,145,23,1,skin),b("Back forearm",3,0,48,44,-20,20,2,brown),b("Front upper arm",1,30,16,48,215,23,6,skin),b("Front forearm",5,0,48,44,-35,20,7,brown),b("Sword",6,0,44,98,-100,15,9,[0.73,0.86,0.95]),b("Back thigh",0,-18,0,55,20,28,0,blue),b("Back shin",8,0,55,55,-15,25,1,brown),b("Front thigh",0,18,0,55,-20,28,5,blue),b("Front shin",10,0,55,55,15,25,6,brown)]
    let a = bones.map(\.angle)
    var walk = a; walk[3] = 200; walk[5] = 160; walk[8] = -30; walk[9] = 30; walk[10] = 30; walk[11] = -10
    return Project(bones: bones, frames: [Frame(time:0,angles:a),Frame(time:1,angles:walk),Frame(time:2,angles:a)])
}
func radians(_ degrees: Double) -> Double { degrees * .pi / 180 }

