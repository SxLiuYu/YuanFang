/**
 * OpenClaw 家庭助手 - 桌面客户端
 * 主进程入口
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage, Notification, globalShortcut } = require('electron');
const path = require('path');
const fs = require('fs');

const log = require('./utils/logger')('Main');
const secureConfig = require('./config');
const DeviceService = require('./services/device');
const ChatService = require('./services/chat');
const WebSocketService = require('./services/websocket');

let mainWindow = null;
let tray = null;
let settings = {};
let deviceService = null;
let chatService = null;
let wsService = null;

const userDataPath = app.getPath('userData');
const settingsPath = path.join(userDataPath, 'settings.json');

const defaultSettings = {
    enableTTS: true,
    enableNotifications: true,
    theme: 'light',
    autoStart: false,
    minimizeToTray: true,
    globalShortcut: 'CommandOrControl+Shift+O',
    contextLength: 10
};

function loadSettings() {
    try {
        if (fs.existsSync(settingsPath)) {
            const data = fs.readFileSync(settingsPath, 'utf8');
            settings = { ...defaultSettings, ...JSON.parse(data) };
        } else {
            settings = { ...defaultSettings };
        }
    } catch (e) {
        log.error('加载设置失败:', e.message);
        settings = { ...defaultSettings };
    }
}

function saveSettings() {
    try {
        fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
    } catch (e) {
        log.error('保存设置失败:', e.message);
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 700,
        minWidth: 600,
        minHeight: 500,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, 'icon.png'),
        title: 'OpenClaw 家庭助手',
        backgroundColor: settings.theme === 'dark' ? '#1a1a2e' : '#f5f5f5',
        show: false
    });
    
    mainWindow.loadFile('index.html');
    
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });
    
    mainWindow.on('close', (event) => {
        if (!app.isQuitting && settings.minimizeToTray) {
            event.preventDefault();
            mainWindow.hide();
        }
    });
    
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function createTray() {
    const iconPath = path.join(__dirname, 'icon.png');
    const icon = nativeImage.createFromPath(iconPath);
    
    tray = new Tray(icon.resize({ width: 16, height: 16 }));
    
    const contextMenu = Menu.buildFromTemplate([
        {
            label: '显示窗口',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    mainWindow.focus();
                }
            }
        },
        { type: 'separator' },
        {
            label: '退出',
            click: () => {
                app.isQuitting = true;
                app.quit();
            }
        }
    ]);
    
    tray.setToolTip('OpenClaw 家庭助手');
    tray.setContextMenu(contextMenu);
    
    tray.on('double-click', () => {
        if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

function registerGlobalShortcut() {
    try {
        globalShortcut.unregisterAll();
        
        if (settings.globalShortcut) {
            globalShortcut.register(settings.globalShortcut, () => {
                if (mainWindow) {
                    if (mainWindow.isVisible()) {
                        mainWindow.hide();
                    } else {
                        mainWindow.show();
                        mainWindow.focus();
                    }
                }
            });
        }
        
        globalShortcut.register('CommandOrControl+Shift+V', () => {
            if (mainWindow) {
                mainWindow.show();
                mainWindow.webContents.send('start-voice-input');
            }
        });
        
    } catch (e) {
        log.error('注册快捷键失败:', e.message);
    }
}

function showNotification(title, body) {
    if (!settings.enableNotifications) return;
    
    if (Notification.isSupported()) {
        const notification = new Notification({
            title: title,
            body: body,
            icon: path.join(__dirname, 'icon.png')
        });
        notification.show();
    }
}

function setupIPC() {
    ipcMain.handle('get-device-auth', () => deviceService.getAuth());
    
    ipcMain.handle('register-device', async () => {
        return new Promise((resolve) => deviceService.register(resolve));
    });
    
    ipcMain.handle('confirm-device', async (event, tempId, confirmCode) => {
        return new Promise((resolve) => deviceService.confirm(tempId, confirmCode, resolve));
    });
    
    ipcMain.handle('get-settings', () => settings);
    
    ipcMain.handle('save-settings', (event, newSettings) => {
        settings = { ...settings, ...newSettings };
        saveSettings();
        return { success: true };
    });
    
    ipcMain.handle('send-chat', async (event, message) => {
        return await chatService.send(message);
    });
    
    ipcMain.handle('show-notification', (event, title, body) => {
        showNotification(title, body);
        return { success: true };
    });
    
    ipcMain.handle('get-config', () => ({
        deviceServerUrl: secureConfig.getDeviceServerUrl(),
        chatServerUrl: secureConfig.getChatServerUrl(),
        isConfigured: secureConfig.isConfigured()
    }));
    
    ipcMain.handle('set-config', (event, config) => {
        if (config.deviceServerUrl) secureConfig.setDeviceServerUrl(config.deviceServerUrl);
        if (config.chatServerUrl) secureConfig.setChatServerUrl(config.chatServerUrl);
        if (config.apiKey) secureConfig.setApiKey(config.apiKey);
        return { success: true };
    });
    
    ipcMain.handle('cancel-chat', () => {
        chatService.cancel();
        return { success: true };
    });
    
    ipcMain.handle('get-ws-status', () => ({
        connected: wsService.isConnected()
    }));
}

function initServices() {
    secureConfig.init();
    
    deviceService = new DeviceService(secureConfig);
    deviceService.init(userDataPath);
    
    chatService = new ChatService(secureConfig, deviceService);
    
    wsService = new WebSocketService(secureConfig, deviceService);
    wsService.on('message', (message) => {
        if (mainWindow) {
            mainWindow.webContents.send('ws-message', message);
        }
    });
    wsService.on('connected', () => {
        if (mainWindow) {
            mainWindow.webContents.send('ws-status', { connected: true });
        }
    });
    wsService.on('disconnected', () => {
        if (mainWindow) {
            mainWindow.webContents.send('ws-status', { connected: false });
        }
    });
}

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
        }
    });
    
    app.whenReady().then(() => {
        initServices();
        loadSettings();
        
        createWindow();
        createTray();
        registerGlobalShortcut();
        setupIPC();
        
        if (!deviceService.isConfirmed()) {
            deviceService.register((result) => {
                if (mainWindow) {
                    mainWindow.webContents.send('auth-status', result);
                }
            });
        } else {
            wsService.connect();
        }
        
        app.on('activate', () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                createWindow();
            }
        });
    });
}

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    app.isQuitting = true;
    globalShortcut.unregisterAll();
    wsService.disconnect();
});