const DOM = {
  authPage: document.getElementById('authPage'),
  mainApp: document.getElementById('mainApp'),
  pendingView: document.getElementById('pendingView'),
  loadingView: document.getElementById('loadingView'),
  errorView: document.getElementById('errorView'),
  authMessage: document.getElementById('authMessage'),
  tempIdDisplay: document.getElementById('tempIdDisplay'),
  confirmBtn: document.getElementById('confirmBtn'),
  retryBtn: document.getElementById('retryBtn'),
  chatMessages: document.getElementById('chatMessages'),
  chatInput: document.getElementById('chatInput'),
  sendBtn: document.getElementById('sendBtn'),
  voiceBtn: document.getElementById('voiceBtn'),
  themeToggle: document.getElementById('themeToggle'),
  wsStatus: document.getElementById('wsStatus')
};

let currentTempId = null;
let messageHistory = [];

function init() {
  checkAuth();
  bindEvents();
  loadTheme();
}

async function checkAuth() {
  const auth = await window.electronAPI.getDeviceAuth();
  if (auth.isConfirmed) {
    showMainApp();
  } else {
    startAuth();
  }
}

async function startAuth() {
  DOM.authPage.classList.add('show');
  DOM.loadingView.style.display = 'block';
  DOM.pendingView.style.display = 'none';
  DOM.errorView.style.display = 'none';
  
  const result = await window.electronAPI.registerDevice();
  
  if (result.confirmed) {
    showMainApp();
  } else if (result.pending) {
    currentTempId = result.tempId;
    showPendingView(result.tempId);
  } else {
    showError(result.error);
  }
}

function showPendingView(tempId) {
  DOM.loadingView.style.display = 'none';
  DOM.pendingView.style.display = 'block';
  DOM.errorView.style.display = 'none';
  
  const code = tempId.substring(tempId.length - 6).toUpperCase();
  DOM.tempIdDisplay.textContent = code.match(/.{1,3}/g).join(' ');
}

function showError(message) {
  DOM.loadingView.style.display = 'none';
  DOM.pendingView.style.display = 'none';
  DOM.errorView.style.display = 'block';
  document.getElementById('errorMessage').textContent = message;
}

async function showMainApp() {
  DOM.authPage.classList.remove('show');
  DOM.mainApp.classList.add('show');
  
  const auth = await window.electronAPI.getDeviceAuth();
  document.getElementById('infoDeviceId').textContent = auth.deviceId;
  
  const wsStatus = await window.electronAPI.getWsStatus();
  updateWsStatus(wsStatus.connected);
}

async function confirmDevice() {
  const code = ['code1', 'code2', 'code3', 'code4', 'code5', 'code6']
    .map(id => document.getElementById(id).value)
    .join('');
  
  if (code.length !== 6) {
    alert('请输入完整的确认码');
    return;
  }
  
  DOM.confirmBtn.disabled = true;
  DOM.confirmBtn.textContent = '确认中...';
  
  const result = await window.electronAPI.confirmDevice(currentTempId, code);
  
  if (result.confirmed) {
    showMainApp();
  } else {
    alert(result.error || '确认失败');
    DOM.confirmBtn.disabled = false;
    DOM.confirmBtn.textContent = '确认';
  }
}

async function sendMessage() {
  const message = DOM.chatInput.value.trim();
  if (!message) return;
  
  addMessage(message, 'user');
  DOM.chatInput.value = '';
  DOM.sendBtn.disabled = true;
  
  messageHistory.push({ role: 'user', content: message });
  
  const result = await window.electronAPI.sendChat(message);
  
  DOM.sendBtn.disabled = false;
  
  if (result.success) {
    addMessage(result.content, 'assistant');
    messageHistory.push({ role: 'assistant', content: result.content });
  } else {
    addMessage(result.error, 'error');
  }
}

function addMessage(content, type) {
  const div = document.createElement('div');
  div.className = `message ${type}`;
  div.textContent = content;
  DOM.chatMessages.appendChild(div);
  DOM.chatMessages.scrollTop = DOM.chatMessages.scrollHeight;
}

function startVoiceInput() {
  if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    
    recognition.onstart = () => { DOM.voiceBtn.textContent = '⏹️'; };
    recognition.onend = () => { DOM.voiceBtn.textContent = '🎤'; };
    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      DOM.chatInput.value = text;
      sendMessage();
    };
    
    recognition.start();
  } else {
    alert('浏览器不支持语音识别');
  }
}

function loadTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const newTheme = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
  if (DOM.themeToggle) {
    DOM.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
}

function updateWsStatus(connected) {
  if (DOM.wsStatus) {
    DOM.wsStatus.className = 'ws-status' + (connected ? ' connected' : '');
  }
}

function bindEvents() {
  DOM.confirmBtn.addEventListener('click', confirmDevice);
  DOM.retryBtn.addEventListener('click', startAuth);
  
  ['code1', 'code2', 'code3', 'code4', 'code5', 'code6'].forEach((id, index) => {
    document.getElementById(id).addEventListener('input', (e) => {
      if (e.target.value && index < 5) {
        document.getElementById(['code1', 'code2', 'code3', 'code4', 'code5', 'code6'][index + 1]).focus();
      }
    });
  });
  
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      const page = item.dataset.page;
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      document.getElementById('page-' + page).classList.add('active');
    });
  });
  
  DOM.sendBtn.addEventListener('click', sendMessage);
  DOM.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
  });
  DOM.voiceBtn.addEventListener('click', startVoiceInput);
  
  if (DOM.themeToggle) {
    DOM.themeToggle.addEventListener('click', toggleTheme);
  }
  
  window.electronAPI.onAuthStatus((result) => {
    if (result.confirmed) {
      showMainApp();
    } else if (result.pending) {
      currentTempId = result.tempId;
      showPendingView(result.tempId);
    }
  });
  
  window.electronAPI.onStartVoiceInput(() => startVoiceInput());
  
  if (window.electronAPI.onWsStatus) {
    window.electronAPI.onWsStatus((status) => updateWsStatus(status.connected));
  }
}

init();