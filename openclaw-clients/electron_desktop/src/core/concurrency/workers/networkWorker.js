// Electron桌面端网络请求Worker
const { parentPort, workerData } = require('worker_threads');
const fetch = require('node-fetch');

// 处理来自主线程的消息
parentPort.on('message', async (message) => {
  try {
    const { type, url, options = {} } = message;
    
    switch (type) {
      case 'httpRequest':
        await handleHttpRequest(url, options);
        break;
      case 'websocketConnect':
        await handleWebSocketConnect(url, options);
        break;
      case 'apiCall':
        await handleApiCall(url, options);
        break;
      default:
        parentPort.postMessage({
          type: 'error',
          error: `Unknown message type: ${type}`,
          workerId: workerData.id
        });
    }
  } catch (error) {
    parentPort.postMessage({
      type: 'error',
      error: error.message,
      workerId: workerData.id
    });
  }
});

async function handleHttpRequest(url, options) {
  try {
    const response = await fetch(url, {
      method: options.method || 'GET',
      headers: options.headers || {},
      body: options.body,
      timeout: options.timeout || 10000
    });

    const data = await response.json();
    
    parentPort.postMessage({
      type: 'httpResponse',
      data: data,
      status: response.status,
      workerId: workerData.id
    });
  } catch (error) {
    parentPort.postMessage({
      type: 'httpError',
      error: error.message,
      workerId: workerData.id
    });
  }
}

async function handleWebSocketConnect(url, options) {
  // WebSocket连接通常在主线程处理，这里作为示例
  parentPort.postMessage({
    type: 'websocketConnected',
    url: url,
    workerId: workerData.id
  });
}

async function handleApiCall(url, options) {
  // 封装API调用逻辑
  const apiOptions = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${options.token || ''}`,
      ...options.headers
    },
    body: JSON.stringify(options.payload || {}),
    timeout: options.timeout || 15000
  };

  try {
    const response = await fetch(url, apiOptions);
    const data = await response.json();
    
    parentPort.postMessage({
      type: 'apiResponse',
      data: data,
      status: response.status,
      workerId: workerData.id
    });
  } catch (error) {
    parentPort.postMessage({
      type: 'apiError',
      error: error.message,
      workerId: workerData.id
    });
  }
}

// Worker启动确认
parentPort.postMessage({
  type: 'workerReady',
  workerId: workerData.id,
  taskType: 'network'
});