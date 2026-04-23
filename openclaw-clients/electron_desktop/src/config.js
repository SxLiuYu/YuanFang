/**
 * 安全配置管理模块
 * 从环境变量或配置文件加载敏感信息
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { app } = require('electron');

class SecureConfig {
    constructor() {
        this.config = {};
        this.configPath = null;
        this.encryptionKey = null;
    }

    init() {
        this.configPath = path.join(app.getPath('userData'), 'secure_config.json');
        this.loadFromEnv();
        this.loadFromFile();
    }

    loadFromEnv() {
        this.config.deviceServerUrl = process.env.OPENCLAW_DEVICE_URL || '';
        this.config.chatServerUrl = process.env.OPENCLAW_CHAT_URL || '';
        this.config.apiKey = process.env.OPENCLAW_API_KEY || '';
    }

    loadFromFile() {
        try {
            if (fs.existsSync(this.configPath)) {
                const data = fs.readFileSync(this.configPath, 'utf8');
                const saved = JSON.parse(data);
                this.config = { ...this.config, ...saved };
            }
        } catch (e) {
            console.error('加载配置文件失败:', e.message);
        }
    }

    saveToFile() {
        try {
            const data = JSON.stringify({
                deviceServerUrl: this.config.deviceServerUrl,
                chatServerUrl: this.config.chatServerUrl,
                apiKey: this.config.apiKey ? this.encrypt(this.config.apiKey) : ''
            }, null, 2);
            fs.writeFileSync(this.configPath, data);
        } catch (e) {
            console.error('保存配置文件失败:', e.message);
        }
    }

    getDeviceServerUrl() {
        return this.config.deviceServerUrl || process.env.OPENCLAW_DEFAULT_DEVICE_URL || 'https://api.openclaw.ai';
    }

    getChatServerUrl() {
        return this.config.chatServerUrl || process.env.OPENCLAW_DEFAULT_CHAT_URL || 'https://chat.openclaw.ai';
    }

    getApiKey() {
        if (!this.config.apiKey) return '';
        if (this.config.apiKey.startsWith('enc:')) {
            return this.decrypt(this.config.apiKey.substring(4));
        }
        return this.config.apiKey;
    }

    setDeviceServerUrl(url) {
        this.config.deviceServerUrl = url;
        this.saveToFile();
    }

    setChatServerUrl(url) {
        this.config.chatServerUrl = url;
        this.saveToFile();
    }

    setApiKey(key) {
        this.config.apiKey = key ? this.encrypt(key) : '';
        this.saveToFile();
    }

    encrypt(text) {
        const key = this.getEncryptionKey();
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
        let encrypted = cipher.update(text, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        return 'enc:' + iv.toString('hex') + ':' + encrypted;
    }

    decrypt(encryptedData) {
        try {
            const key = this.getEncryptionKey();
            const parts = encryptedData.split(':');
            if (parts.length !== 2) return encryptedData;
            const iv = Buffer.from(parts[0], 'hex');
            const encrypted = parts[1];
            const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
            let decrypted = decipher.update(encrypted, 'hex', 'utf8');
            decrypted += decipher.final('utf8');
            return decrypted;
        } catch (e) {
            console.error('解密失败:', e.message);
            return '';
        }
    }

    getEncryptionKey() {
        if (!this.encryptionKey) {
            const machineId = require('os').hostname() + process.env.USERNAME;
            this.encryptionKey = crypto.createHash('sha256').update(machineId).digest();
        }
        return this.encryptionKey;
    }

    isConfigured() {
        return !!(this.getApiKey() || this.config.deviceToken);
    }

    setDeviceToken(token) {
        this.config.deviceToken = token;
        this.saveToFile();
    }

    getDeviceToken() {
        return this.config.deviceToken || '';
    }

    hasDeviceToken() {
        return !!(this.config.deviceToken);
    }

    clear() {
        this.config = {};
        try {
            if (fs.existsSync(this.configPath)) {
                fs.unlinkSync(this.configPath);
            }
        } catch (e) {
            console.error('清除配置失败:', e.message);
        }
    }
}

const secureConfig = new SecureConfig();

module.exports = secureConfig;