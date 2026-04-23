/**
 * WebSocket 服务
 * 处理实时通信和设备同步
 */

const WebSocket = require('ws');
const log = require('../utils/logger')('WebSocketService');

class WebSocketService {
    constructor(secureConfig, deviceService) {
        this.secureConfig = secureConfig;
        this.deviceService = deviceService;
        this.ws = null;
        this.reconnectTimer = null;
        this.reconnectDelay = 5000;
        this.maxReconnectDelay = 60000;
        this.listeners = new Map();
    }
    
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            log.debug('WebSocket 已连接');
            return;
        }
        
        const serverUrl = this.secureConfig.getDeviceServerUrl();
        const wsUrl = serverUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
        const deviceToken = this.deviceService.deviceAuth?.deviceToken;
        
        if (!deviceToken) {
            log.warn('无设备令牌，跳过 WebSocket 连接');
            return;
        }
        
        try {
            log.info('连接 WebSocket:', wsUrl);
            this.ws = new WebSocket(wsUrl, {
                headers: {
                    'Authorization': 'Bearer ' + deviceToken
                }
            });
            
            this.ws.on('open', () => {
                log.info('WebSocket 已连接');
                this.reconnectDelay = 5000;
                this.emit('connected');
                
                this.ws.send(JSON.stringify({
                    type: 'auth',
                    deviceId: this.deviceService.getAuth().deviceId
                }));
            });
            
            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    log.debug('收到消息:', message.type);
                    this.emit('message', message);
                    
                    if (message.type) {
                        this.emit(message.type, message.data);
                    }
                } catch (e) {
                    log.error('解析消息失败:', e.message);
                }
            });
            
            this.ws.on('close', (code, reason) => {
                log.warn('WebSocket 关闭:', code, reason.toString());
                this.emit('disconnected', { code, reason: reason.toString() });
                this.scheduleReconnect();
            });
            
            this.ws.on('error', (error) => {
                log.error('WebSocket 错误:', error.message);
                this.emit('error', error);
            });
            
        } catch (e) {
            log.error('连接 WebSocket 失败:', e.message);
            this.scheduleReconnect();
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectTimer) return;
        
        log.info(`将在 ${this.reconnectDelay / 1000} 秒后重连`);
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
        }, this.reconnectDelay);
    }
    
    disconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        log.info('WebSocket 已断开');
    }
    
    send(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
            return true;
        }
        return false;
    }
    
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }
    
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    log.error('事件处理错误:', e.message);
                }
            });
        }
    }
    
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

module.exports = WebSocketService;