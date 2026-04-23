/**
 * 设备认证服务
 * 处理设备注册、确认、令牌管理
 */

const http = require('http');
const os = require('os');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const log = require('../utils/logger')('DeviceService');

class DeviceService {
    constructor(secureConfig) {
        this.secureConfig = secureConfig;
        this.authPath = null;
        this.deviceAuth = {
            deviceId: null,
            deviceToken: null,
            isConfirmed: false,
            tempId: null
        };
    }
    
    init(userDataPath) {
        this.authPath = path.join(userDataPath, 'device_auth.json');
        this.loadDeviceAuth();
    }
    
    generateDeviceId() {
        const hostname = os.hostname();
        const platform = os.platform();
        const cpus = os.cpus();
        const cpuModel = cpus.length > 0 ? cpus[0].model : 'unknown';
        const id = crypto.createHash('md5').update(hostname + platform + cpuModel).digest('hex');
        return 'desktop_' + id.substring(0, 16);
    }
    
    loadDeviceAuth() {
        try {
            if (fs.existsSync(this.authPath)) {
                const data = fs.readFileSync(this.authPath, 'utf8');
                this.deviceAuth = JSON.parse(data);
                log.info('设备认证信息已加载');
            } else {
                this.deviceAuth.deviceId = this.generateDeviceId();
                this.saveDeviceAuth();
                log.info('新设备ID已生成:', this.deviceAuth.deviceId);
            }
        } catch (e) {
            log.error('加载设备认证失败:', e.message);
            this.deviceAuth.deviceId = this.generateDeviceId();
        }
    }
    
    saveDeviceAuth() {
        try {
            fs.writeFileSync(this.authPath, JSON.stringify(this.deviceAuth, null, 2));
            if (this.deviceAuth.deviceToken) {
                this.secureConfig.setDeviceToken(this.deviceAuth.deviceToken);
            }
        } catch (e) {
            log.error('保存设备认证失败:', e.message);
        }
    }
    
    getAuth() {
        return {
            deviceId: this.deviceAuth.deviceId,
            isConfirmed: this.deviceAuth.isConfirmed,
            tempId: this.deviceAuth.tempId
        };
    }
    
    isConfirmed() {
        return this.deviceAuth.isConfirmed;
    }
    
    register(callback) {
        const deviceServerUrl = this.secureConfig.getDeviceServerUrl();
        
        const requestData = JSON.stringify({
            device_id: this.deviceAuth.deviceId,
            device_name: os.hostname() || 'Windows Desktop',
            device_model: os.type() + ' ' + os.release()
        });
        
        const serverUrl = new URL(deviceServerUrl);
        
        const options = {
            hostname: serverUrl.hostname,
            port: serverUrl.port || 8081,
            path: '/device/register',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(requestData)
            }
        };
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    
                    if (json.confirmed) {
                        this.deviceAuth.deviceToken = json.token;
                        this.deviceAuth.isConfirmed = true;
                        this.saveDeviceAuth();
                        log.info('设备已确认');
                        callback({ confirmed: true, token: json.token });
                        
                    } else if (json.status === 'pending') {
                        this.deviceAuth.tempId = json.temp_id;
                        this.saveDeviceAuth();
                        log.info('等待确认，temp_id:', json.temp_id);
                        callback({ pending: true, tempId: json.temp_id });
                        
                    } else {
                        callback({ error: json.message || '注册失败' });
                    }
                } catch (e) {
                    log.error('解析响应失败:', e.message);
                    callback({ error: '解析响应失败' });
                }
            });
        });
        
        req.on('error', (e) => {
            log.error('注册请求失败:', e.message);
            callback({ error: '网络请求失败: ' + e.message });
        });
        
        req.write(requestData);
        req.end();
    }
    
    confirm(tempId, confirmCode, callback) {
        const deviceServerUrl = this.secureConfig.getDeviceServerUrl();
        const requestData = JSON.stringify({
            temp_id: tempId,
            confirm_code: confirmCode.toUpperCase()
        });
        
        const serverUrl = new URL(deviceServerUrl);
        
        const options = {
            hostname: serverUrl.hostname,
            port: serverUrl.port || 8081,
            path: '/device/confirm',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(requestData)
            }
        };
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    
                    if (json.confirmed) {
                        this.deviceAuth.deviceToken = json.token;
                        this.deviceAuth.isConfirmed = true;
                        this.saveDeviceAuth();
                        log.info('设备确认成功');
                        callback({ confirmed: true, token: json.token });
                    } else {
                        callback({ error: json.message || '确认失败' });
                    }
                } catch (e) {
                    callback({ error: '解析响应失败' });
                }
            });
        });
        
        req.on('error', (e) => {
            callback({ error: '网络请求失败: ' + e.message });
        });
        
        req.write(requestData);
        req.end();
    }
}

module.exports = DeviceService;