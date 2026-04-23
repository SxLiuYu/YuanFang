//
//  Message.swift
//  OpenClawClients
//
//  消息模型
//

import Foundation

enum MessageType: String, Codable {
    case user
    case assistant
    case error
}

struct Message: Identifiable, Codable {
    let id: UUID
    let content: String
    let type: MessageType
    let timestamp: Date
    
    init(id: UUID = UUID(), content: String, type: MessageType, timestamp: Date = Date()) {
        self.id = id
        self.content = content
        self.type = type
        self.timestamp = timestamp
    }
}
