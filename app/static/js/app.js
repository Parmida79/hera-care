// API Base URL
const API_BASE = window.location.origin;
const API_PUBLIC = `${API_BASE}/public/hera-care/v1`;
const API_RESTRICTED = `${API_BASE}/restricted/hera-care/v1`;

// State Management
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let chatSessionId = null;
let currentQuestionType = null;

// Section mapping
const SECTIONS = {
    'onboarding': { label: 'اطلاعات پایه', index: 0 },
    'symptoms': { label: 'علائم', index: 1 },
    'lifestyle': { label: 'سبک زندگی', index: 2 },
    'vitals': { label: 'علائم حیاتی', index: 3 },
    'lab_results': { label: 'آزمایش', index: 4 },
    'ultrasound': { label: 'سونوگرافی', index: 5 }
};

let currentSection = 'onboarding';
let sectionStates = {};

// Generic API call with error handling
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
const panelModal = document.getElementById('panelModal');
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');
const closeModal = document.getElementById('closeModal');
const closeChatModal = document.getElementById('closeChatModal');
const closePanelModal = document.getElementById('closePanelModal');
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
const toast = document.getElementById('toast');
const quickReplies = document.getElementById('quickReplies');
const panelBtn = document.getElementById('panelBtn');
const hamburgerBtn = document.getElementById('hamburgerBtn');
const hamburgerDropdown = document.getElementById('hamburgerDropdown');

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
    showSignup?.addEventListener('click', (e) => { e.preventDefault(); switchAuthForm('signup'); });
    showLogin?.addEventListener('click', (e) => { e.preventDefault(); switchAuthForm('login'); });
    loginFormElement?.addEventListener('submit', handleLogin);
    signupFormElement?.addEventListener('submit', handleSignup);

    // Chat
    startAssessmentBtn?.addEventListener('click', openChatModal);
    startChatBtn?.addEventListener('click', startChat);
    closeChatModal?.addEventListener('click', () => { chatModal.classList.remove('active'); resetChat(); });
    sendBtn?.addEventListener('click', sendMessage);
    chatInput?.addEventListener('keypress', (e) => { if (e.key === 'Enter' && !chatInput.disabled) sendMessage(); });

    // Quick reply buttons
    document.querySelectorAll('.btn-quick').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.value;
            sendMessage();
        });
    });

    // Panel
    panelBtn?.addEventListener('click', openPanelModal);
    closePanelModal?.addEventListener('click', () => panelModal.classList.remove('active'));

    // Hamburger menu
    hamburgerBtn?.addEventListener('click', toggleHamburgerMenu);
    document.getElementById('menuAssessment')?.addEventListener('click', (e) => {
        e.preventDefault();
        closeHamburgerMenu();
        openChatModal();
    });
    document.getElementById('menuHistory')?.addEventListener('click', (e) => {
        e.preventDefault();
        closeHamburgerMenu();
        openPanelModal();
        switchPanelTab('history');
    });
    document.getElementById('menuProfile')?.addEventListener('click', (e) => {
        e.preventDefault();
        closeHamburgerMenu();
        openPanelModal();
        switchPanelTab('profile');
    });
    document.getElementById('menuLogout')?.addEventListener('click', (e) => {
        e.preventDefault();
        closeHamburgerMenu();
        handleLogout();
    });

    // Panel tabs
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.addEventListener('click', () => switchPanelTab(tab.dataset.tab));
    });

    // New assessment from panel
    document.getElementById('newAssessmentBtn')?.addEventListener('click', () => {
        panelModal.classList.remove('active');
        openChatModal();
    });

    // Close modals on outside click
    authModal?.addEventListener('click', (e) => { if (e.target === authModal) closeAuthModal(); });
    chatModal?.addEventListener('click', (e) => { if (e.target === chatModal) { chatModal.classList.remove('active'); resetChat(); } });
    panelModal?.addEventListener('click', (e) => { if (e.target === panelModal) panelModal.classList.remove('active'); });

    // Close hamburger on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.hamburger-menu')) closeHamburgerMenu();
    });
}

// ---- Auth Functions ----
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
        const data = await apiCall(`${API_PUBLIC}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

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
        await apiCall(`${API_PUBLIC}/signup`, {
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

        showToast('ثبت نام موفقیت‌آمیز بود. در حال ورود...', 'success');
        signupFormElement.reset();

        // Auto-login after signup
        document.getElementById('loginUsername').value = username;
        document.getElementById('loginPassword').value = password;
        switchAuthForm('login');
        await handleLogin(new Event('submit'));
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function loadCurrentUser() {
    try {
        currentUser = await apiCall(`${API_RESTRICTED}/me`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        updateUIForLoggedInUser();
    } catch (error) {
        showToast(error.message, 'error');
        handleLogout();
        throw error;
    }
}

function updateUIForLoggedInUser() {
    authButtons.classList.add('hidden');
    userMenu.classList.remove('hidden');

    // Update hamburger dropdown user info
    const dropdownUserInfo = document.getElementById('dropdownUserInfo');
    if (dropdownUserInfo) {
        const displayName = currentUser.firstName
            ? `${currentUser.firstName} ${currentUser.lastName || ''}`
            : currentUser.username;
        dropdownUserInfo.innerHTML = `
            <div class="user-greeting">👋 ${displayName}</div>
            <div class="user-email">${currentUser.email || currentUser.username}</div>
        `;
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');

    authButtons.classList.remove('hidden');
    userMenu.classList.add('hidden');
    closeHamburgerMenu();

    showToast('خروج موفقیت‌آمیز', 'success');
}

// ---- Hamburger Menu ----
function toggleHamburgerMenu() {
    hamburgerBtn.classList.toggle('active');
    hamburgerDropdown.classList.toggle('hidden');
}

function closeHamburgerMenu() {
    hamburgerBtn?.classList.remove('active');
    hamburgerDropdown?.classList.add('hidden');
}

// ---- Chat Functions ----
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
        const data = await apiCall(`${API_RESTRICTED}/chat/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: 'سلام' })
        });

        chatSessionId = data.sessionId;

        // Hide welcome screen
        chatBody.querySelector('.chat-welcome')?.remove();

        // Show bot message
        addMessage('bot', data.message);
        updateProgress(data.progress);
        if (data.sectionSummary) updateSectionTracker(data.sectionSummary);

        // Show quick replies for first question (consent)
        showQuickReplies(true);

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
    showQuickReplies(false);

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
            if (data.prediction) {
                displayFinalResult(data);
            } else {
                // User exited
                addMessage('bot', data.message);
                setTimeout(() => {
                    chatModal.classList.remove('active');
                    resetChat();
                }, 3000);
            }
        } else {
            addMessage('bot', data.message);
            updateProgress(data.progress);
            if (data.sectionSummary) updateSectionTracker(data.sectionSummary);

            // Determine if this is a yes/no question
            const isYesNo = data.message.includes('بله/خیر') ||
                           data.message.includes('بله / خیر') ||
                           data.message.includes('ادامه می‌دهید');

            if (isYesNo) {
                showQuickReplies(true);
                chatInput.disabled = true;
                sendBtn.disabled = true;
            } else {
                showQuickReplies(false);
                chatInput.disabled = false;
                sendBtn.disabled = false;
                chatInput.focus();
            }
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        showToast(error.message, 'error');

        setTimeout(() => {
            chatModal.classList.remove('active');
            resetChat();
        }, 3000);
    }
}

function showQuickReplies(show) {
    if (show) {
        quickReplies.classList.remove('hidden');
        chatInput.disabled = true;
        sendBtn.disabled = true;
    } else {
        quickReplies.classList.add('hidden');
    }
}

function addMessage(type, text) {
    const messageDiv = document.createElement('div');

    // Check if this is a section transition
    if (text.includes('━━━━━━')) {
        messageDiv.className = 'section-transition';
        const lines = text.split('\n').filter(line => line.trim());
        const titleLine = lines.find(line => line.includes('بخش'));
        const descLines = lines.filter(line =>
            !line.includes('━') && !line.includes('بخش') && !line.includes('✅') && line.trim()
        );

        messageDiv.innerHTML = `
            <h4>${titleLine || ''}</h4>
            ${descLines.map(l => `<p>${l}</p>`).join('')}
        `;
    } else {
        messageDiv.className = `message ${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'bot' ? '🌸' : '👤';

        const content = document.createElement('div');
        content.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = text.replace(/\n/g, '<br>');

        content.appendChild(messageText);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
    }

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

    const progressText = document.getElementById('progressText');
    if (progressText) {
        progressText.textContent = `${percentage}٪`;
    }
}

function updateSectionTracker(sectionData) {
    if (!sectionData) return;

    sectionStates = sectionData;

    const steps = document.querySelectorAll('.section-step');
    const connectors = document.querySelectorAll('.section-connector');
    const sectionLabel = document.getElementById('currentSectionLabel');

    let lastCompletedIndex = -1;
    let activeIndex = -1;

    steps.forEach((step) => {
        const section = step.dataset.section;
        const state = sectionData[section];

        step.classList.remove('active', 'completed', 'skipped');

        if (state === 'تکمیل شده') {
            step.classList.add('completed');
            step.querySelector('.section-dot').textContent = '✓';
            lastCompletedIndex = SECTIONS[section].index;
        } else if (state === 'رد شده') {
            step.classList.add('skipped');
            step.querySelector('.section-dot').textContent = '—';
            lastCompletedIndex = SECTIONS[section].index;
        } else if (state === 'نرسیده' && activeIndex === -1) {
            step.classList.add('active');
            activeIndex = SECTIONS[section].index;
            currentSection = section;

            if (sectionLabel) {
                sectionLabel.textContent = SECTIONS[section].label;
            }
        }
    });

    connectors.forEach((connector, index) => {
        connector.classList.remove('completed', 'active');
        if (index < lastCompletedIndex) {
            connector.classList.add('completed');
        } else if (index === lastCompletedIndex) {
            connector.classList.add('active');
        }
    });
}

function displayFinalResult(data) {
    const prediction = data.prediction;
    const resultDiv = document.createElement('div');
    resultDiv.className = 'result-card';

    const icon = prediction.hasPcos ? '⚠️' : '✅';
    const title = prediction.hasPcos ? 'احتمال PCOS' : 'بدون علائم PCOS';
    const confidencePercent = (prediction.confidence * 100).toFixed(1);

    let riskClass = 'risk-low';
    if (prediction.riskLevel === 'متوسط') riskClass = 'risk-medium';
    else if (prediction.riskLevel === 'بالا') riskClass = 'risk-high';
    else if (prediction.riskLevel === 'بسیار بالا') riskClass = 'risk-very-high';

    let recommendationsHTML = '';
    prediction.recommendations.forEach(rec => {
        recommendationsHTML += `<li>${rec}</li>`;
    });

    let sectionBadgesHTML = '';
    if (sectionStates) {
        Object.entries(sectionStates).forEach(([section, state]) => {
            const label = SECTIONS[section]?.label || section;
            if (state === 'تکمیل شده') {
                sectionBadgesHTML += `<span class="completed-badge done">✓ ${label}</span>`;
            } else if (state === 'رد شده') {
                sectionBadgesHTML += `<span class="completed-badge skipped">— ${label}</span>`;
            }
        });
    }

    resultDiv.innerHTML = `
        <div class="result-header">
            <div class="result-icon">${icon}</div>
            <h3 class="result-title">${title}</h3>
            <p class="result-confidence">اطمینان: ${confidencePercent}٪</p>
            <span class="result-risk ${riskClass}">سطح ریسک: ${prediction.riskLevel}</span>
            <div class="result-sections-completed">
                ${sectionBadgesHTML}
            </div>
        </div>
        <div class="result-section">
            <h4>💡 توصیه‌ها:</h4>
            <ul class="result-list">
                ${recommendationsHTML}
            </ul>
        </div>
        <div class="result-warning">
            ⚠️ این تشخیص کمکی است و جایگزین مشاوره پزشکی نیست.
            <br>
            💡 هرچه بخش‌های بیشتری را تکمیل کنید، دقت تشخیص بالاتر می‌رود.
        </div>
    `;

    chatBody.appendChild(resultDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    chatInput.disabled = true;
    sendBtn.disabled = true;
    showQuickReplies(false);
    updateProgress({ percentage: 100 });

    // Mark all sections done in tracker
    document.querySelectorAll('.section-step').forEach(step => {
        if (!step.classList.contains('skipped')) {
            step.classList.remove('active');
            step.classList.add('completed');
            step.querySelector('.section-dot').textContent = '✓';
        }
    });
    document.querySelectorAll('.section-connector').forEach(conn => {
        conn.classList.add('completed');
    });
}

function resetChat() {
    chatSessionId = null;
    currentQuestionType = null;
    sectionStates = {};

    chatBody.innerHTML = `
        <div class="chat-welcome">
            <div class="welcome-icon">🌸</div>
            <h4>ارزیابی هوشمند PCOS</h4>
            <p>این ارزیابی شامل ۶ بخش است:</p>
            <div class="section-overview">
                <div class="overview-item">
                    <span class="overview-num">۱</span>
                    <span>اطلاعات پایه</span>
                    <span class="overview-badge required">الزامی</span>
                </div>
                <div class="overview-item">
                    <span class="overview-num">۲</span>
                    <span>علائم ظاهری</span>
                    <span class="overview-badge required">الزامی</span>
                </div>
                <div class="overview-item">
                    <span class="overview-num">۳</span>
                    <span>سبک زندگی</span>
                    <span class="overview-badge required">الزامی</span>
                </div>
                <div class="overview-item">
                    <span class="overview-num">۴</span>
                    <span>علائم حیاتی</span>
                    <span class="overview-badge optional">اختیاری</span>
                </div>
                <div class="overview-item">
                    <span class="overview-num">۵</span>
                    <span>نتایج آزمایش</span>
                    <span class="overview-badge optional">اختیاری</span>
                </div>
                <div class="overview-item">
                    <span class="overview-num">۶</span>
                    <span>سونوگرافی</span>
                    <span class="overview-badge optional">اختیاری</span>
                </div>
            </div>
            <p class="welcome-note">⏱ زمان تقریبی: ۳ تا ۵ دقیقه</p>
            <button class="btn btn-primary" id="startChatBtn">شروع ارزیابی</button>
        </div>
    `;

    chatInput.value = '';
    chatInput.disabled = true;
    sendBtn.disabled = true;
    showQuickReplies(false);
    progressFill.style.width = '0%';
    document.getElementById('progressText').textContent = '۰٪';

    // Reset section tracker
    document.querySelectorAll('.section-step').forEach((step, i) => {
        step.classList.remove('active', 'completed', 'skipped');
        if (i === 0) step.classList.add('active');
        step.querySelector('.section-dot').textContent = `${i + 1}`;
    });
    document.querySelectorAll('.section-connector').forEach(conn => {
        conn.classList.remove('completed', 'active');
    });
    document.getElementById('currentSectionLabel').textContent = 'اطلاعات پایه';

    // Re-attach start button
    document.getElementById('startChatBtn')?.addEventListener('click', startChat);
}

// ---- Patient Panel Functions ----
function openPanelModal() {
    if (!authToken) {
        showToast('لطفاً ابتدا وارد شوید', 'warning');
        openAuthModal('login');
        return;
    }
    panelModal.classList.add('active');
    loadPanelData();
}

function switchPanelTab(tabName) {
    document.querySelectorAll('.panel-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    document.querySelectorAll('.panel-tab-content').forEach(content => {
        content.classList.toggle('active', content.dataset.tab === tabName);
    });
}

async function loadPanelData() {
    if (!currentUser) return;

    // Overview tab
    const name = currentUser.firstName
        ? `${currentUser.firstName} ${currentUser.lastName || ''}`
        : currentUser.username;

    document.getElementById('panelName').textContent = name;
    document.getElementById('panelDob').textContent = currentUser.dateOfBirth || '-';
    document.getElementById('panelWeight').textContent = currentUser.weightKg
        ? `${currentUser.weightKg} کیلوگرم` : '-';
    document.getElementById('panelHeight').textContent = currentUser.heightCm
        ? `${currentUser.heightCm} سانتی‌متر` : '-';
    document.getElementById('panelBmi').textContent = currentUser.bmi
        ? currentUser.bmi.toFixed(1) : '-';
    document.getElementById('panelMarital').textContent =
        translateMaritalStatus(currentUser.maritalStatus);

    // Profile tab
    document.getElementById('profileFirstName').value = currentUser.firstName || '';
    document.getElementById('profileLastName').value = currentUser.lastName || '';
    document.getElementById('profileEmail').value = currentUser.email || '';
    document.getElementById('profilePhone').value = currentUser.phoneNumber || '';

    // Load assessment history
    await loadAssessmentHistory();
}

function translateMaritalStatus(status) {
    const map = {
        'single': 'مجرد',
        'married': 'متأهل',
        'divorced': 'مطلقه',
        'widow': 'بیوه',
        'unknown': '-'
    };
    return map[status] || '-';
}

async function loadAssessmentHistory() {
    // TODO: Create a backend endpoint for this
    // For now, show placeholder
    const historyList = document.getElementById('historyList');
    const assessmentsList = document.getElementById('assessmentsList');

    try {
        // Placeholder until backend endpoint is ready
        historyList.innerHTML = '<p class="no-data">در حال بارگذاری...</p>';
        assessmentsList.innerHTML = '<p class="no-data">در حال بارگذاری...</p>';

        // When backend is ready:
        // const data = await apiCall(`${API_RESTRICTED}/history`, {
        //     headers: { 'Authorization': `Bearer ${authToken}` }
        // });
        // renderHistory(data);

        historyList.innerHTML = '<p class="no-data">تاریخچه‌ای موجود نیست</p>';
        assessmentsList.innerHTML = '<p class="no-data">ارزیابی قبلی موجود نیست</p>';
    } catch (error) {
        historyList.innerHTML = '<p class="no-data">خطا در بارگذاری</p>';
    }
}

// ---- Toast Notification ----
function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ---- Smooth Scroll ----
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            this.classList.add('active');
        }
    });
});
