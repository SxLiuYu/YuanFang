//
//  ChatViewModel.swift
//  OpenClawClients
//
//  聊天视图模型
//

import Foundation
import Speech
import Combine

class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isListening: Bool = false
    @Published var isConnected: Bool = false
    @Published var apiKey: String = ""
    @Published var wsUrl: String = "ws://localhost:8080/ws"
    @Published var isTyping: Bool = false
    @Published var chatHistory: [ChatSession] = []
    
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var audioEngine: AVAudioEngine?
    private var webSocketTask: URLSessionWebSocketTask?
    private var conversationManager: ConversationManager?
    private var speechSynthesizer: AVSpeechSynthesizer?
    
    struct ChatSession: Identifiable, Codable {
        let id: String
        let preview: String
        let timestamp: Date
        let messages: [Message]
    }
    
    init() {
        conversationManager = ConversationManager()
        loadSettings()
        setupSpeechRecognizer()
        setupTTS()
        connectWebSocket()
        loadMessages()
    }
    
    private func loadSettings() {
        apiKey = UserDefaults.standard.string(forKey: "dashscope_api_key") ?? ""
        wsUrl = UserDefaults.standard.string(forKey: "ws_url") ?? "ws://localhost:8080/ws"
    }
    
    func saveSettings(apiKey: String, wsUrl: String) {
        self.apiKey = apiKey
        self.wsUrl = wsUrl
        UserDefaults.standard.set(apiKey, forKey: "dashscope_api_key")
        UserDefaults.standard.set(wsUrl, forKey: "ws_url")
        connectWebSocket()
    }
    
    private func setupTTS() {
        speechSynthesizer = AVSpeechSynthesizer()
    }
    
    func speak(_ text: String) {
        guard UserDefaults.standard.bool(forKey: "tts_enabled") else { return }
        
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "zh-CN")
        utterance.rate = 0.5
        speechSynthesizer?.speak(utterance)
    }
    
    private func loadMessages() {
        if let session = conversationManager?.getContext().last {
            messages.append(Message(
                content: session.content,
                type: session.role == "user" ? .user : .assistant
            ))
        } else {
            addWelcomeMessage()
        }
        chatHistory = conversationManager?.getHistory().map { session in
            ChatSession(id: session.id, preview: session.preview, timestamp: session.timestamp, messages: session.messages)
        } ?? []
    }
    
    private func addWelcomeMessage() {
        messages.append(Message(
            content: "你好！我是你的家庭助手。支持语音、TTS 朗读、多轮对话和历史记录。",
            type: .assistant
        ))
    }
    
    private func setupSpeechRecognizer() {
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "zh-CN"))
        audioEngine = AVAudioEngine()
        
        // 请求语音识别权限
        SFSpeechRecognizer.requestAuthorization { authStatus in
            DispatchQueue.main.async {
                switch authStatus {
                case .authorized:
                    print("语音识别已授权")
                case .denied, .restricted, .notDetermined:
                    print("语音识别未授权")
                @unknown default:
                    break
                }
            }
        }
    }
    
    func startListening() {
        guard let speechRecognizer = speechRecognizer, speechRecognizer.isAvailable else {
            addMessage("语音识别不可用", type: .error)
            return
        }
        
        do {
            try startRecording()
            isListening = true
        } catch {
            addMessage("语音识别启动失败：\(error.localizedDescription)", type: .error)
        }
    }
    
    func stopListening() {
        stopRecording()
        isListening = false
    }
    
    private func startRecording() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else {
            throw NSError(domain: "ChatViewModel", code: 1, userInfo: [NSLocalizedDescriptionKey: "无法创建识别请求"])
        }
        
        recognitionRequest.shouldReportPartialResults = true
        
        let inputNode = audioEngine!.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, when in
            self.recognitionRequest?.append(buffer)
        }
        
        audioEngine!.prepare()
        try audioEngine!.start()
        
        recognitionTask = speechRecognizer!.recognitionTask(with: recognitionRequest!) { result, error in
            if let result = result {
                let transcript = result.bestTranscription.formattedString
                // 可以实时更新 UI
            }
            
            if error != nil || result?.isFinal == true {
                self.stopRecording()
                if let transcript = result?.bestTranscription.formattedString {
                    self.sendMessage(transcript)
                }
                self.isListening = false
            }
        }
    }
    
    private func stopRecording() {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        recognitionRequest = nil
        recognitionTask?.cancel()
    }
    
    func sendMessage(_ text: String) {
        guard !text.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        
        addMessage(text, type: .user)
        conversationManager?.addToContext(role: "user", content: text)
        isTyping = true
        
        if isConnected, webSocketTask != nil {
            sendViaWebSocket(text)
        } else {
            callDashScopeAPI(text)
        }
    }
    
    private func sendViaWebSocket(_ text: String) {
        let message: [String: Any] = [
            "type": "message",
            "content": text,
            "apiKey": apiKey
        ]
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: message)
            webSocketTask?.send(.data(jsonData)) { error in
                if let error = error {
                    print("WebSocket 发送失败：\(error)")
                }
            }
        } catch {
            print("JSON 序列化失败：\(error)")
        }
    }
    
    private func callDashScopeAPI(_ text: String) {
        guard !apiKey.isEmpty else {
            DispatchQueue.main.async {
                self.isTyping = false
                self.addMessage("请先在设置中配置 DashScope API 密钥", type: .error)
            }
            return
        }
        
        guard let url = URL(string: "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation") else {
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "model": "qwen-max",
            "input": [
                "messages": [
                    ["role": "system", "content": "你是一个家庭助手，请理解用户的语音指令并提供相应的帮助。"],
                    ["role": "user", "content": text]
                ]
            ],
            "parameters": [
                "temperature": 0.7,
                "top_p": 0.8,
                "max_tokens": 500
            ]
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        } catch {
            print("请求体序列化失败：\(error)")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isTyping = false
                
                if let error = error {
                    self.addMessage("请求失败：\(error.localizedDescription)", type: .error)
                    return
                }
                
                guard let data = data else {
                    self.addMessage("无响应数据", type: .error)
                    return
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let output = json["output"] as? [String: Any],
                       let choices = output["choices"] as? [[String: Any]],
                       let firstChoice = choices.first,
                       let message = firstChoice["message"] as? [String: Any],
                       let content = message["content"] as? String {
                        self.addMessage(content, type: .assistant)
                    } else {
                        self.addMessage("API 响应格式错误", type: .error)
                    }
                } catch {
                    self.addMessage("解析响应失败：\(error.localizedDescription)", type: .error)
                }
            }
        }.resume()
    }
    
    private func connectWebSocket() {
        guard let url = URL(string: wsUrl) else { return }
        
        webSocketTask?.cancel()
        
        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)
        
        webSocketTask?.resume()
        isConnected = true
        
        receiveWebSocketMessage()
    }
    
    private func receiveWebSocketMessage() {
        webSocketTask?.receive { result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    DispatchQueue.main.async {
                        self.isTyping = false
                        self.addMessage(text, type: .assistant)
                    }
                case .data(let data):
                    DispatchQueue.main.async {
                        self.isTyping = false
                        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                           let type = json["type"] as? String,
                           type == "response",
                           let content = json["content"] as? String {
                            self.addMessage(content, type: .assistant)
                        }
                    }
                @unknown default:
                    break
                }
                self.receiveWebSocketMessage()
                
            case .failure(let error):
                print("WebSocket 接收错误：\(error)")
                DispatchQueue.main.async {
                    self.isConnected = false
                }
            }
        }
    }
    
    func addMessage(_ content: String, type: MessageType) {
        messages.append(Message(content: content, type: type))
        
        // 保存到历史记录
        if type == .assistant {
            conversationManager?.addToHistory(messages: messages.map { msg in
                ConversationManager.Message(role: msg.type == .user ? "user" : "assistant", content: msg.content)
            })
            chatHistory = conversationManager?.getHistory().map { session in
                ChatSession(id: session.id, preview: session.preview, timestamp: session.timestamp, messages: session.messages)
            } ?? []
            
            // TTS 朗读
            speak(content)
        }
    }
    
    func clearMessages() {
        messages.removeAll()
        conversationManager?.clearContext()
        addWelcomeMessage()
    }
    
    func clearHistory() {
        conversationManager?.clearHistory()
        chatHistory.removeAll()
    }
    
    func loadSession(_ session: ChatSession) {
        messages = session.messages
        conversationManager?.conversationContext = session.messages.map { msg in
            ConversationManager.Message(role: msg.type == .user ? "user" : "assistant", content: msg.content)
        }
    }
}
