//
//  HistoryView.swift
//  OpenClawClients
//
//  历史记录视图
//

import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var viewModel: ChatViewModel
    @Environment(\.dismiss) var dismiss
    @State private var selectedSession: ChatViewModel.ChatSession?
    
    var body: some View {
        NavigationView {
            List {
                if viewModel.chatHistory.isEmpty {
                    Text("暂无历史记录")
                        .foregroundColor(.gray)
                        .padding()
                } else {
                    ForEach(viewModel.chatHistory, id: \.id) { session in
                        Button(action: {
                            selectedSession = session
                        }) {
                            VStack(alignment: .leading, spacing: 8) {
                                Text(session.preview)
                                    .font(.body)
                                    .lineLimit(2)
                                
                                Text(session.timestamp, style: .date)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("📜 对话历史")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("清空") {
                        viewModel.clearHistory()
                    }
                    .foregroundColor(.red)
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("完成") {
                        dismiss()
                    }
                }
            }
            .alert(item: $selectedSession) { session in
                Alert(
                    title: Text("查看历史对话"),
                    message: Text(session.preview),
                    primaryButton: .default(Text("加载")) {
                        viewModel.loadSession(session)
                        dismiss()
                    },
                    secondaryButton: .cancel()
                )
            }
        }
    }
}

struct HistoryView_Previews: PreviewProvider {
    static var previews: some View {
        HistoryView()
            .environmentObject(ChatViewModel())
    }
}
