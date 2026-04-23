/**
 * 日志工具
 * 统一日志输出，支持日志级别
 */

const isDev = process.env.NODE_ENV === 'development';

class Logger {
    constructor(module) {
        this.module = module;
    }
    
    _format(level, message) {
        const timestamp = new Date().toISOString();
        return `[${timestamp}] [${level}] [${this.module}] ${message}`;
    }
    
    debug(message, ...args) {
        if (isDev) {
            console.debug(this._format('DEBUG', message), ...args);
        }
    }
    
    info(message, ...args) {
        console.info(this._format('INFO', message), ...args);
    }
    
    warn(message, ...args) {
        console.warn(this._format('WARN', message), ...args);
    }
    
    error(message, ...args) {
        console.error(this._format('ERROR', message), ...args);
    }
}

module.exports = (module) => new Logger(module);