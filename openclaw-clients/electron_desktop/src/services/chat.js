/**
 * AI 对话服务
 * 处理与 AI 服务器的通信
 */

const http = require('http');
const log = require('../utils/logger')('ChatService');

class ChatService {
    constructor(secureConfig, deviceService) {
        this.secureConfig = secureConfig;
        this.deviceService = deviceService;
        this.currentRequest = null;
    }
    
    cancel() {
        if (this.currentRequest) {
            this.currentRequest.destroy();
            this.currentRequest = null;
            log.info('请求已取消');
        }
    }
    
    async send(message, contextHistory = []) {
        return new Promise((resolve) => {
            const chatServerUrl = this.secureConfig.getChatServerUrl();
            const apiKey = this.secureConfig.getApiKey();
            const deviceToken = this.deviceService.getAuth().isConfirmed ? 
                this.deviceService.deviceAuth?.deviceToken : null;
            
            const serverUrl = new URL(chatServerUrl);
            
            const messages = [
                { 
                    role: 'system', 
                    content: '你是 OpenClaw 家庭助手，一个友好、智能的家庭助理。你可以帮助用户管理家庭事务、回答问题、提供建议。请用简洁自然的语言回复。' 
                },
                ...contextHistory,
                { role: 'user', content: message }
            ];
            
            const requestData = JSON.stringify({
                model: 'qwen3.5-plus',
                messages: messages
            });
            
            log.debug('发送聊天请求到:', chatServerUrl);
            
            const authToken = deviceToken || apiKey;
            
            const options = {
                hostname: serverUrl.hostname,
                port: serverUrl.port || 10352,
                path: '/v1/chat/completions',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(requestData)
                }
            };
            
            if (authToken) {
                options.headers['Authorization'] = 'Bearer ' + authToken;
            }
            
            this.currentRequest = http.request(options, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    this.currentRequest = null;
                    log.debug('服务器响应:', res.statusCode);
                    
                    try {
                        const json = JSON.parse(data);
                        
                        if (res.statusCode === 200 && json.choices && json.choices.length > 0) {
                            const content = json.choices[0].message?.content || json.choices[0].text;
                            resolve({ success: true, content: content });
                        } else if (json.error) {
                            const errorMsg = typeof json.error === 'string' ? json.error :
                                            (json.error.message || JSON.stringify(json.error));
                            resolve({ error: '服务器错误: ' + errorMsg });
                        } else if (json.reply) {
                            resolve({ success: true, content: json.reply });
                        } else if (json.response) {
                            resolve({ success: true, content: json.response });
                        } else {
                            resolve({ error: '服务器返回格式错误' });
                        }
                    } catch (e) {
                        resolve({ error: '解析响应失败: ' + e.message });
                    }
                });
            });
            
            this.currentRequest.on('error', (e) => {
                this.currentRequest = null;
                log.error('请求错误:', e.message);
                resolve({ error: '无法连接服务器: ' + e.message });
            });
            
            this.currentRequest.setTimeout(60000, () => {
                this.currentRequest.destroy();
                this.currentRequest = null;
                resolve({ error: '请求超时' });
            });
            
            this.currentRequest.write(requestData);
            this.currentRequest.end();
        });
    }
}

module.exports = ChatService;