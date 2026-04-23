//
//  OpenClawClientsApp.swift
//  OpenClawClients
//
//  OpenClaw 家庭助手 - iOS 客户端
//

import SwiftUI

@main
struct OpenClawClientsApp: App {
    @StateObject private var viewModel = ChatViewModel()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(viewModel)
        }
    }
}
