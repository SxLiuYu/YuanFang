//
//  ConversationManager.swift
//  OpenClawClients
//
//  对话管理器 - 多轮对话上下文和历史记录
//

import Foundation

class ConversationManager {
    private let contextKey = "conversation_context"
    private let historyKey = "chat_history"
    private let maxContextSize = 20
    private let maxHistoryCount = 50
    
    struct Message: Codable {
        let id: String
        let role: String
        let content: String
        let timestamp: Date
        
        init(role: String, content: String) {
            self.id = UUID().uuidString
            self.role = role
            self.content = content
            self.timestamp = Date()
        }
    }
    
    struct ChatSession: Codable {
        let id: String
        let preview: String
        let timestamp: Date
        let messages: [Message]
        
        init(preview: String, messages: [Message]) {
            self.id = UUID().uuidString
            self.preview = preview
            self.timestamp = Date()
            self.messages = messages
        }
    }
    
    private var conversationContext: [Message] = []
    private var chatHistory: [ChatSession] = []
    
    init() {
        loadContext()
        loadHistory()
    }
    
    // MARK: - Context Management
    
    func addToContext(role: String, content: String) {
        conversationContext.append(Message(role: role, content: content))
        
        // 限制上下文大小
        if conversationContext.count > maxContextSize {
            conversationContext = Array(conversationContext.suffix(maxContextSize))
        }
        
        saveContext()
    }
    
    func getContext() -> [Message] {
        return conversationContext
    }
    
    func clearContext() {
        conversationContext.removeAll()
        saveContext()
    }
    
    func getContextForAPI(maxMessages: Int) -> [Message] {
        var result: [Message] = []
        result.append(Message(role: "system", content: "你是一个家庭助手，请理解用户的语音指令并提供相应的帮助。保持对话连贯性。"))
        
        let start = max(0, conversationContext.count - maxMessages)
        result.append(contentsOf: conversationContext.suffix(from: start))
        
        return result
    }
    
    private func saveContext() {
        if let encoded = try? JSONEncoder().encode(conversationContext) {
            UserDefaults.standard.set(encoded, forKey: contextKey)
        }
    }
    
    private func loadContext() {
        if let data = UserDefaults.standard.data(forKey: contextKey),
           let decoded = try? JSONDecoder().decode([Message].self, from: data) {
            conversationContext = decoded
        }
    }
    
    // MARK: - History Management
    
    func addToHistory(messages: [Message]) {
        guard let firstUserMessage = messages.first(where: { $0.role == "user" }) else { return }
        
        let session = ChatSession(preview: firstUserMessage.content, messages: messages)
        chatHistory.insert(session, at: 0)
        
        // 限制历史记录数量
        if chatHistory.count > maxHistoryCount {
            chatHistory = Array(chatHistory.prefix(maxHistoryCount))
        }
        
        saveHistory()
    }
    
    func getHistory() -> [ChatSession] {
        return chatHistory
    }
    
    func clearHistory() {
        chatHistory.removeAll()
        saveHistory()
    }
    
    private func saveHistory() {
        if let encoded = try? JSONEncoder().encode(chatHistory) {
            UserDefaults.standard.set(encoded, forKey: historyKey)
        }
    }
    
    private func loadHistory() {
        if let data = UserDefaults.standard.data(forKey: historyKey),
           let decoded = try? JSONDecoder().decode([ChatSession].self, from: data) {
            chatHistory = decoded
        }
    }
}
