// Electron桌面端并发管理 - Worker线程管理器
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const path = require('path');

class WorkerManager {
  constructor() {
    this.workers = new Map();
    this.workerIdCounter = 0;
  }

  /**
   * 创建并启动一个新的Worker线程
   * @param {string} taskType - 任务类型 ('network', 'dataProcessing', 'fileIO', 'ml')
   * @param {object} options - Worker选项
   * @returns {Promise<Worker>} 启动的Worker实例
   */
  async createWorker(taskType, options = {}) {
    const workerId = `worker_${this.workerIdCounter++}_${taskType}`;
    const workerPath = path.join(__dirname, 'workers', `${taskType}Worker.js`);
    
    return new Promise((resolve, reject) => {
      const worker = new Worker(workerPath, {
        workerData: {
          id: workerId,
          ...options
        },
        ...options
      });

      worker.on('online', () => {
        console.log(`Worker ${workerId} started`);
        this.workers.set(workerId, worker);
        resolve(worker);
      });

      worker.on('error', (error) => {
        console.error(`Worker ${workerId} error:`, error);
        this.workers.delete(workerId);
        reject(error);
      });

      worker.on('exit', (code) => {
        console.log(`Worker ${workerId} exited with code ${code}`);
        this.workers.delete(workerId);
      });
    });
  }

  /**
   * 向指定Worker发送消息
   * @param {string} workerId - Worker ID
   * @param {any} message - 要发送的消息
   */
  sendMessageToWorker(workerId, message) {
    const worker = this.workers.get(workerId);
    if (worker) {
      worker.postMessage(message);
    } else {
      console.warn(`Worker ${workerId} not found`);
    }
  }

  /**
   * 终止指定Worker
   * @param {string} workerId - Worker ID
   */
  terminateWorker(workerId) {
    const worker = this.workers.get(workerId);
    if (worker) {
      worker.terminate();
      this.workers.delete(workerId);
    }
  }

  /**
   * 终止所有Workers
   */
  terminateAllWorkers() {
    for (const [id, worker] of this.workers) {
      worker.terminate();
    }
    this.workers.clear();
  }

  /**
   * 获取活跃Worker数量
   */
  getActiveWorkerCount() {
    return this.workers.size;
  }
}

// 单例模式
const workerManager = new WorkerManager();
module.exports = workerManager;