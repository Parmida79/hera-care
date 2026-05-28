// API Base URL
const API_BASE = window.location.origin;
const API_PUBLIC = `${API_BASE}/public/hera-care/v1`;
const API_RESTRICTED = `${API_BASE}/restricted/hera-care/v1`;

// State Management
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let chatSessionId = null;

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            let errorMessage = 'خطا در ارتباط با سرور';

            // Try to get detailed error from response FIRST
            try {
                const errorData = await response.json();
                if (errorData.detail) {
                    errorMessage = errorData.detail;
                }
            } catch (e) {
                // Use default error message based on status
                switch (response.status) {
                    case 400:
                        errorMessage = 'درخواست نامعتبر';
                        break;
                    case 401:
                        errorMessage = 'نشست شما منقضی شده است. لطفاً دوباره وارد شوید';
                        break;
                    case 403:
                        errorMessage = 'دسترسی غیرمجاز';
                        break;
                    case 404:
                        errorMessage = 'اطلاعات درخواستی یافت نشد';
                        break;
                    case 409:
                        errorMessage = 'این اطلاعات قبلاً ثبت شده است';
                        break;
                    case 422:
                        errorMessage = 'اطلاعات وارد شده معتبر نیست';
                        break;
                    case 500:
                        errorMessage = 'خطای سرور. لطفاً بعداً تلاش کنید';
                        break;
                }
            }

            const error = new Error(errorMessage);
            error.status = response.status; // Attach status code
            throw error;
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('خطا در ارتباط با سرور. لطفاً اتصال اینترنت خود را بررسی کنید');
        }
        throw error;
    }
}

// DOM Elements
const authModal = document.getElementById('authModal');
const chatModal = document.getElementById('chatModal');
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');
const logoutBtn = document.getElementById('logoutBtn');
const closeModal = document.getElementById('closeModal');
const closeChatModal = document.getElementById('closeChatModal');
const showSignup = document.getElementById('showSignup');
const showLogin = document.getElementById('showLogin');
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const loginFormElement = document.getElementById('loginFormElement');
const signupFormElement = document.getElementById('signupFormElement');
const startAssessmentBtn = document.getElementById('startAssessmentBtn');
const startChatBtn = document.getElementById('startChatBtn');
const chatBody = document.getElementById('chatBody');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const progressFill = document.getElementById('progressFill');
const authButtons = document.getElementById('authButtons');
const userMenu = document.getElementById('userMenu');
const userName = document.getElementById('userName');
const toast = document.getElementById('toast');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    if (authToken) {
        loadCurrentUser();
    }
    initEventListeners();
});

// Event Listeners
function initEventListeners() {
    // Auth Modal
    loginBtn?.addEventListener('click', () => openAuthModal('login'));
    signupBtn?.addEventListener('click', () => openAuthModal('signup'));
    closeModal?.addEventListener('click', closeAuthModal);
    showSignup?.addEventListener('click', (e) => {
        e.preventDefault();
        switchAuthForm('signup');
    });
    showLogin?.addEventListener('click', (e) => {
        e.preventDefault();
        switchAuthForm('login');
    });

    // Forms
    loginFormElement?.addEventListener('submit', handleLogin);
    signupFormElement?.addEventListener('submit', handleSignup);

    // Logout
    logoutBtn?.addEventListener('click', handleLogout);

    // Chat
    startAssessmentBtn?.addEventListener('click', openChatModal);
    startChatBtn?.addEventListener('click', startChat);
    closeChatModal?.addEventListener('click', () => {
        chatModal.classList.remove('active');
        resetChat();
    });
    sendBtn?.addEventListener('click', sendMessage);
    chatInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !chatInput.disabled) {
            sendMessage();
        }
    });

    // Close modal on outside click
    authModal?.addEventListener('click', (e) => {
        if (e.target === authModal) closeAuthModal();
    });
    chatModal?.addEventListener('click', (e) => {
        if (e.target === chatModal) {
            chatModal.classList.remove('active');
            resetChat();
        }
    });
}

// Auth Functions
function openAuthModal(type = 'login') {
    authModal.classList.add('active');
    switchAuthForm(type);
}

function closeAuthModal() {
    authModal.classList.remove('active');
}

function switchAuthForm(type) {
    if (type === 'login') {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
    } else {
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_PUBLIC}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error('نام کاربری یا رمز عبور اشتباه است');
        }

        const data = await response.json();
        authToken = data.accessToken;
        localStorage.setItem('authToken', authToken);

        await loadCurrentUser();
        closeAuthModal();
        showToast('خوش آمدید!', 'success');
        loginFormElement.reset();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const username = document.getElementById('signupUsername').value;
    const password = document.getElementById('signupPassword').value;
    const email = document.getElementById('signupEmail').value;
    const firstName = document.getElementById('signupFirstName').value;
    const lastName = document.getElementById('signupLastName').value;

    try {
        const response = await fetch(`${API_PUBLIC}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                password,
                email: email || null,
                firstName: firstName || null,
                lastName: lastName || null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'خطا در ثبت نام');
        }

        showToast('ثبت نام موفقیت‌آمیز بود. لطفاً وارد شوید', 'success');
        signupFormElement.reset();
        switchAuthForm('login');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function loadCurrentUser() {
    try {
        const response = await fetch(`${API_RESTRICTED}/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (!response.ok) {
            throw new Error('خطا در بارگذاری اطلاعات کاربر');
        }

        currentUser = await response.json();
        updateUIForLoggedInUser();
    } catch (error) {
        handleLogout();
    }
}

function updateUIForLoggedInUser() {
    authButtons.classList.add('hidden');
    userMenu.classList.remove('hidden');
    userName.textContent = currentUser.firstName || currentUser.username;
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');

    authButtons.classList.remove('hidden');
    userMenu.classList.add('hidden');

    showToast('خروج موفقیت‌آمیز', 'success');
}

// Chat Functions
function openChatModal() {
    if (!authToken) {
        showToast('لطفاً ابتدا وارد شوید', 'warning');
        openAuthModal('login');
        return;
    }
    chatModal.classList.add('active');
}

async function startChat() {
    try {
        const response = await fetch(`${API_RESTRICTED}/chat/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: 'سلام' })
        });

        if (!response.ok) {
            throw new Error('خطا در شروع گفتگو');
        }

        const data = await response.json();
        chatSessionId = data.sessionId;

        // Hide welcome screen
        chatBody.querySelector('.chat-welcome')?.remove();

        // Show bot message
        addMessage('bot', data.message);
        updateProgress(data.progress);

        // Enable input
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || !chatSessionId) return;

    addMessage('user', message);
    chatInput.value = '';
    chatInput.disabled = true;
    sendBtn.disabled = true;

    const typingId = addTypingIndicator();

    try {
        const data = await apiCall(`${API_RESTRICTED}/chat/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sessionId: chatSessionId,
                message: message
            })
        });

        removeTypingIndicator(typingId);

        if (data.finished) {
            displayFinalResult(data);
        } else {
            addMessage('bot', data.message);
            updateProgress(data.progress);
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        showToast(error.message, 'error');

        // Close modal after error
        setTimeout(() => {
            chatModal.classList.remove('active');
            resetChat();
        }, 3000);  // Give user time to read error
    }
}

function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'bot' ? '🌸' : '👤';

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;

    content.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatBody.appendChild(messageDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'message bot';
    typingDiv.innerHTML = `
        <div class="message-avatar">🌸</div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatBody.appendChild(typingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    document.getElementById(id)?.remove();
}

function updateProgress(progress) {
    const percentage = progress.percentage;
    progressFill.style.width = `${percentage}%`;
}

function displayFinalResult(data) {
    const prediction = data.prediction;
    const resultDiv = document.createElement('div');
    resultDiv.className = 'result-card';

    const icon = prediction.hasPcos ? '⚠️' : '✅';
    const title = prediction.hasPcos ? 'احتمال PCOS' : 'بدون علائم PCOS';

    let recommendationsHTML = '';
    prediction.recommendations.forEach(rec => {
        recommendationsHTML += `<li>${rec}</li>`;
    });

    resultDiv.innerHTML = `
        <div class="result-header">
            <div class="result-icon">${icon}</div>
            <h3 class="result-title">${title}</h3>
            <p class="result-confidence">اطمینان: ${(prediction.confidence * 100).toFixed(1)}%</p>
            <p>سطح ریسک: ${prediction.riskLevel}</p>
        </div>

        <div class="result-section">
            <h4>💡 توصیه‌ها:</h4>
            <ul class="result-list">
                ${recommendationsHTML}
            </ul>
        </div>

        <div class="result-warning">
            ⚠️ این تشخیص کمکی است و جایگزین مشاوره پزشکی نیست.
        </div>
    `;

    chatBody.appendChild(resultDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Disable input
    chatInput.disabled = true;
    sendBtn.disabled = true;

    updateProgress({ percentage: 100 });
}

function resetChat() {
    chatSessionId = null;
    chatBody.innerHTML = `
        <div class="chat-welcome">
            <div class="welcome-icon">🌸</div>
            <h4>سلام! خوش آمدید</h4>
            <p>برای شروع ارزیابی، روی دکمه زیر کلیک کنید</p>
            <button class="btn btn-primary" id="startChatBtn">شروع گفتگو</button>
        </div>
    `;
    chatInput.value = '';
    chatInput.disabled = true;
    sendBtn.disabled = true;
    progressFill.style.width = '0%';

    // Re-attach event listener
    document.getElementById('startChatBtn').addEventListener('click', startChat);
}

// Toast Notification
function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Smooth Scroll for Navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });

            // Update active nav link
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            this.classList.add('active');
        }
    });
});