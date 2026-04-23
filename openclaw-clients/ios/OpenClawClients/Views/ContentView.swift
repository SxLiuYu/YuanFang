//
//  ContentView.swift
//  OpenClawClients
//
//  主界面视图
//

import SwiftUI
import Speech

struct ContentView: View {
    @EnvironmentObject var viewModel: ChatViewModel
    @State private var inputText: String = ""
    @State private var showSettings: Bool = false
    @State private var showHistory: Bool = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // 状态栏
                StatusBarView(isConnected: viewModel.isConnected, isListening: viewModel.isListening)
                
                // 消息列表
                MessageListView(messages: viewModel.messages, isTyping: viewModel.isTyping)
                
                // 输入区域
                InputAreaView(
                    inputText: $inputText,
                    isListening: viewModel.isListening,
                    onSend: { viewModel.sendMessage(inputText); inputText = "" },
                    onToggleListening: {
                        if viewModel.isListening {
                            viewModel.stopListening()
                        } else {
                            viewModel.startListening()
                        }
                    },
                    onClear: { viewModel.clearMessages() }
                )
            }
            .navigationTitle("🤖 OpenClaw 家庭助手")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showHistory.toggle() }) {
                        Image(systemName: "clock.fill")
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showSettings.toggle() }) {
                        Image(systemName: "gearshape.fill")
                    }
                }
            }
            .sheet(isPresented: $showHistory) {
                HistoryView()
                    .environmentObject(viewModel)
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
                    .environmentObject(viewModel)
            }
        }
    }
}

// MARK: - 状态栏
struct StatusBarView: View {
    let isConnected: Bool
    let isListening: Bool
    
    var body: some View {
        HStack {
            Circle()
                .fill(statusColor)
                .frame(width: 10, height: 10)
                .animation(.easeInOut(duration: 0.3), value: statusColor)
            
            Text(statusText)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
    }
    
    private var statusColor: Color {
        if isListening {
            return .blue
        } else if isConnected {
            return .green
        } else {
            return .gray
        }
    }
    
    private var statusText: String {
        if isListening {
            return "正在听..."
        } else if isConnected {
            return "已连接"
        } else {
            return "未连接"
        }
    }
}

// MARK: - 消息列表
struct MessageListView: View {
    let messages: [Message]
    let isTyping: Bool
    @ScrollViewReader private var scrollProxy
    
    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 12) {
                ForEach(messages) { message in
                    MessageBubble(message: message)
                }
                
                if isTyping {
                    TypingIndicatorView()
                        .id("typing")
                }
            }
            .padding()
        }
        .onChange(of: messages.count) { _ in
            scrollToBottom()
        }
        .onChange(of: isTyping) { _ in
            if isTyping {
                scrollToBottom()
            }
        }
    }
    
    private func scrollToBottom() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            if let lastId = messages.last?.id {
                withAnimation {
                    scrollProxy.scrollTo(lastId, anchor: .bottom)
                }
            } else if isTyping {
                withAnimation {
                    scrollProxy.scrollTo("typing", anchor: .bottom)
                }
            }
        }
    }
}

// MARK: - 消息气泡
struct MessageBubble: View {
    let message: Message
    
    var body: some View {
        HStack {
            if message.type == .user {
                Spacer()
            }
            
            Text(message.content)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(messageColor)
                .foregroundColor(messageForegroundColor)
                .cornerRadius(16)
            
            if message.type == .assistant {
                Spacer()
            }
        }
    }
    
    private var messageColor: Color {
        switch message.type {
        case .user:
            return Color(.systemBlue)
        case .assistant:
            return Color(.systemGray5)
        case .error:
            return Color(.systemRed).opacity(0.2)
        }
    }
    
    private var messageForegroundColor: Color {
        switch message.type {
        case .user:
            return .white
        case .assistant:
            return .primary
        case .error:
            return .red
        }
    }
}

// MARK: - 打字指示器
struct TypingIndicatorView: View {
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(Color(.systemBlue))
                .frame(width: 8, height: 8)
                .scaleEffect(yOffset)
                .animation(Animation.easeInOut(duration: 0.6).repeatForever(autoreverses: true).delay(0), value: yOffset)
            
            Circle()
                .fill(Color(.systemBlue))
                .frame(width: 8, height: 8)
                .scaleEffect(yOffset2)
                .animation(Animation.easeInOut(duration: 0.6).repeatForever(autoreverses: true).delay(0.2), value: yOffset2)
            
            Circle()
                .fill(Color(.systemBlue))
                .frame(width: 8, height: 8)
                .scaleEffect(yOffset3)
                .animation(Animation.easeInOut(duration: 0.6).repeatForever(autoreverses: true).delay(0.4), value: yOffset3)
        }
        .padding()
        .background(Color(.systemGray5))
        .cornerRadius(16)
    }
    
    @State private var yOffset: CGFloat = 0.6
    @State private var yOffset2: CGFloat = 0.6
    @State private var yOffset3: CGFloat = 0.6
}

// MARK: - 输入区域
struct InputAreaView: View {
    @Binding var inputText: String
    let isListening: Bool
    let onSend: () -> Void
    let onToggleListening: () -> Void
    let onClear: () -> Void
    
    var body: some View {
        VStack(spacing: 8) {
            // 控制按钮
            HStack(spacing: 12) {
                Button(action: onToggleListening) {
                    HStack {
                        Image(systemName: isListening ? "stop.circle.fill" : "mic.fill")
                        Text(isListening ? "停止语音" : "开始语音")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isListening ? Color.red : Color(.systemBlue))
                    .foregroundColor(.white)
                    .cornerRadius(10)
                }
                
                Button(action: onClear) {
                    Image(systemName: "trash")
                        .frame(width: 50, height: 44)
                        .background(Color(.systemGray5))
                        .cornerRadius(10)
                }
            }
            .padding(.horizontal)
            
            // 文本输入
            HStack(spacing: 8) {
                TextField("输入消息...", text: $inputText)
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(10)
                
                Button(action: onSend) {
                    Image(systemName: "paperplane.fill")
                        .font(.title2)
                        .foregroundColor(.white)
                        .frame(width: 50, height: 44)
                        .background(inputText.isEmpty ? Color.gray : Color(.systemBlue))
                        .cornerRadius(10)
                }
                .disabled(inputText.isEmpty)
            }
            .padding(.horizontal)
            .padding(.bottom, 8)
        }
        .padding(.top, 8)
        .background(Color(.systemBackground))
    }
}

// MARK: - 设置视图
struct SettingsView: View {
    @EnvironmentObject var viewModel: ChatViewModel
    @Environment(\.dismiss) var dismiss
    @State private var apiKey: String = ""
    @State private var wsUrl: String = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("API 配置")) {
                    SecureField("DashScope API Key", text: $apiKey)
                        .textContentType(.password)
                    
                    TextField("WebSocket 服务器地址", text: $wsUrl)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                }
                
                Section(footer: Text("设置会自动保存")) {
                    Button("保存设置") {
                        viewModel.saveSettings(apiKey: apiKey, wsUrl: wsUrl)
                        dismiss()
                    }
                    .foregroundColor(.blue)
                }
            }
            .navigationTitle("设置")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("完成") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                apiKey = viewModel.apiKey
                wsUrl = viewModel.wsUrl
            }
        }
    }
}

// MARK: - 预览
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .environmentObject(ChatViewModel())
    }
}
