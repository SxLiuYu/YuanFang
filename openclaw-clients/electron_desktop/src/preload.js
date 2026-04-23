const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getDeviceAuth: () => ipcRenderer.invoke('get-device-auth'),
  registerDevice: () => ipcRenderer.invoke('register-device'),
  confirmDevice: (tempId, confirmCode) => ipcRenderer.invoke('confirm-device', tempId, confirmCode),

  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),

  sendChat: (message) => ipcRenderer.invoke('send-chat', message),
  cancelChat: () => ipcRenderer.invoke('cancel-chat'),

  showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body),

  getConfig: () => ipcRenderer.invoke('get-config'),
  setConfig: (config) => ipcRenderer.invoke('set-config', config),

  getWsStatus: () => ipcRenderer.invoke('get-ws-status'),

  onAuthStatus: (callback) => {
    ipcRenderer.on('auth-status', (event, data) => callback(data));
  },
  
  onStartVoiceInput: (callback) => {
    ipcRenderer.on('start-voice-input', () => callback());
  },
  
  onWsStatus: (callback) => {
    ipcRenderer.on('ws-status', (event, data) => callback(data));
  },
  
  onWsMessage: (callback) => {
    ipcRenderer.on('ws-message', (event, data) => callback(data));
  },
  
  removeListener: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});