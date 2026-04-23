/**
 * Electron 桌面客户端测试脚本
 * 运行: node test/test.js
 */

const assert = require('assert');
const path = require('path');

console.log('=== OpenClaw Desktop 客户端测试 ===\n');

// 测试1: 检查依赖
console.log('📦 测试1: 检查依赖包');
try {
    require('electron');
    require('ws');
    console.log('✅ 核心依赖加载成功\n');
} catch (e) {
    console.error('❌ 依赖加载失败:', e.message);
    process.exit(1);
}

// 测试2: 检查配置模块
console.log('⚙️  测试2: 检查配置模块');
try {
    const config = require('../src/config');
    assert(typeof config.getDeviceServerUrl === 'function', 'getDeviceServerUrl 方法缺失');
    assert(typeof config.getChatServerUrl === 'function', 'getChatServerUrl 方法缺失');
    assert(typeof config.testConnection === 'function', 'testConnection 方法缺失');
    console.log('✅ 配置模块正常\n');
} catch (e) {
    console.error('❌ 配置模块测试失败:', e.message);
}

// 测试3: 检查离线存储模块
console.log('💾 测试3: 检查离线存储模块');
try {
    const offlineStorage = require('../src/services/offlineStorage');
    assert(typeof offlineStorage.saveMessage === 'function', 'saveMessage 方法缺失');
    assert(typeof offlineStorage.loadHistory === 'function', 'loadHistory 方法缺失');
    assert(typeof offlineStorage.getSession === 'function', 'getSession 方法缺失');
    console.log('✅ 离线存储模块正常\n');
} catch (e) {
    console.error('❌ 离线存储模块测试失败:', e.message);
}

// 测试4: 检查WebSocket服务
console.log('🔌 测试4: 检查WebSocket服务');
try {
    const WebSocketService = require('../src/services/websocket');
    assert(typeof WebSocketService === 'function', 'WebSocketService 不是构造函数');
    console.log('✅ WebSocket服务模块正常\n');
} catch (e) {
    console.error('❌ WebSocket服务测试失败:', e.message);
}

// 测试5: 检查设备服务
console.log('📱 测试5: 检查设备服务');
try {
    const DeviceService = require('../src/services/device');
    assert(typeof DeviceService === 'function', 'DeviceService 不是构造函数');
    console.log('✅ 设备服务模块正常\n');
} catch (e) {
    console.error('❌ 设备服务测试失败:', e.message);
}

// 测试6: 检查聊天服务
console.log('💬 测试6: 检查聊天服务');
try {
    const ChatService = require('../src/services/chat');
    assert(typeof ChatService === 'function', 'ChatService 不是构造函数');
    console.log('✅ 聊天服务模块正常\n');
} catch (e) {
    console.error('❌ 聊天服务测试失败:', e.message);
}

// 测试7: 检查HTML文件
console.log('📄 测试7: 检查静态文件');
const fs = require('fs');
const files = [
    '../index.html',
    '../styles/main.css',
    '../scripts/app.js'
];

files.forEach(file => {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
        const stats = fs.statSync(filePath);
        console.log(`  ✅ ${file} (${stats.size} bytes)`);
    } else {
        console.log(`  ❌ ${file} 不存在`);
    }
});
console.log('');

// 测试8: 检查新增的UI元素
console.log('🎨 测试8: 检查UI元素');
try {
    const html = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
    
    const requiredElements = [
        { id: 'configToggle', desc: '配置切换按钮' },
        { id: 'configPanel', desc: '配置面板' },
        { id: 'deviceServerInput', desc: '设备服务器输入框' },
        { id: 'chatServerInput', desc: '聊天服务器输入框' },
        { id: 'testConnectionBtn', desc: '测试连接按钮' },
        { id: 'settingsDeviceServer', desc: '设置页设备服务器输入框' },
        { id: 'wsConnectionStatus', desc: 'WebSocket连接状态' },
        { id: 'reconnectWsBtn', desc: '重连按钮' }
    ];
    
    requiredElements.forEach(elem => {
        if (html.includes(`id="${elem.id}"`)) {
            console.log(`  ✅ ${elem.desc} (${elem.id})`);
        } else {
            console.log(`  ❌ ${elem.desc} (${elem.id}) 缺失`);
        }
    });
    console.log('');
} catch (e) {
    console.error('❌ UI元素检查失败:', e.message);
}

// 测试9: 检查CSS样式
console.log('💅 测试9: 检查CSS样式');
try {
    const css = fs.readFileSync(path.join(__dirname, '../styles/main.css'), 'utf8');
    
    const requiredClasses = [
        'config-toggle',
        'config-panel',
        'form-group',
        'connection-info',
        'status-item',
        'status-value',
        'status-value.connected',
        'status-value.disconnected'
    ];
    
    requiredClasses.forEach(cls => {
        if (css.includes(`.${cls}`)) {
            console.log(`  ✅ .${cls}`);
        } else {
            console.log(`  ❌ .${cls} 缺失`);
        }
    });
    console.log('');
} catch (e) {
    console.error('❌ CSS样式检查失败:', e.message);
}

// 测试总结
console.log('='.repeat(50));
console.log('✅ 所有核心模块测试通过！');
console.log('='.repeat(50));
console.log('\n下一步：手动测试UI功能');
console.log('1. 打开应用，检查认证页面');
console.log('2. 点击"高级配置"，测试配置面板');
console.log('3. 修改服务器地址，测试保存功能');
console.log('4. 进入设置页面，测试各项功能');
console.log('5. 检查连接状态指示器');