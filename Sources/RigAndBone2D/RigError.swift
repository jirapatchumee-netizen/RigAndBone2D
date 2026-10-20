import Foundation
struct RigError: Error, LocalizedError {
    let code: String
    let message: String
    var context: String? = nil
    var errorDescription: String? { message }
}
