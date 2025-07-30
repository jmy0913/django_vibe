class ChatBot {
    constructor() {
        this.chatMessages = document.querySelector('#chat-messages');
        this.chatInput = document.querySelector('#chat-input');
        this.sendButton = document.querySelector('#send-btn');
        this.levelButtons = document.querySelectorAll('input[name="btnradio"]');
        this.newChatBtn = document.querySelector('#new-chat-btn');
        this.sessionsContainer = document.querySelector('#chat-sessions-container');
        
        this.currentLevel = 'basic';
        this.isLoading = false;
        this.sessionId = '';
        this.chatHistory = [];
        this.currentSessionId = null;
        this.sessions = [];
        
        // CSRF 토큰 가져오기
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        this.init();
    }
    
    init() {
        // 이벤트 리스너 등록
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // 새 채팅 버튼 이벤트
        if (this.newChatBtn) {
            this.newChatBtn.addEventListener('click', () => this.startNewChat());
        }
        
        // 레벨 선택 이벤트
        this.levelButtons.forEach(button => {
            button.addEventListener('change', (e) => {
                if (e.target.checked) {
                    console.log('레벨 버튼 변경:', e.target.id);
                    const levelNumber = e.target.id.replace('btnradio', '');
                    this.setLevel(levelNumber);
                }
            });
        });
        
        // 초기 레벨 설정 (기본값: 초급)
        this.setLevel('1');
        
        // 페이지 로드 시 세션 목록 불러오기
        this.loadSessions().then(() => {
            // 세션이 없으면 새 세션 시작
            if (this.sessions.length === 0) {
                this.startNewChat();
            }
        });
    }
    
    async loadSessions() {
        try {
            const response = await fetch('/api/sessions/');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('세션 데이터 로드:', data);
            
            if (data.sessions) {
                this.sessions = data.sessions;
                this.renderSessions();
                
                // 첫 번째 세션이 있으면 로드 (단, loadSessions을 직접 호출한 경우가 아닐 때만)
                if (this.sessions.length > 0 && !this.currentSessionId) {
                    this.loadSession(this.sessions[0].session_id);
                }
            } else {
                this.sessions = [];
                this.renderSessions();
            }
        } catch (error) {
            console.error('세션 로드 오류:', error);
            this.sessions = [];
            this.renderSessions();
        }
    }
    
    renderSessions() {
        const emptyMessage = this.sessionsContainer.querySelector('#empty-sessions');
        if (emptyMessage) {
            emptyMessage.remove();
        }
        
        this.sessionsContainer.innerHTML = '';
        
        if (this.sessions.length === 0) {
            this.sessionsContainer.innerHTML = '<div class="chat-list__empty" id="empty-sessions">저장된 대화가 없습니다.</div>';
            return;
        }
        
        this.sessions.forEach(session => {
            const sessionElement = this.createSessionElement(session);
            this.sessionsContainer.appendChild(sessionElement);
        });
    }
    
    createSessionElement(session) {
        const sessionDiv = document.createElement('div');
        sessionDiv.className = 'chat-session-item';
        sessionDiv.dataset.sessionId = session.session_id;
        
        if (session.session_id === this.currentSessionId) {
            sessionDiv.classList.add('active');
        }
        
        const title = session.title || '새로운 대화';
        const time = new Date(session.updated_at).toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        sessionDiv.innerHTML = `
            <div class="session-title">${title}</div>
            <div class="session-time">${time}</div>
            <div class="session-delete" onclick="chatBot.deleteSession('${session.session_id}')">
                <i class="bi bi-trash"></i>
            </div>
        `;
        
        sessionDiv.addEventListener('click', (e) => {
            if (!e.target.closest('.session-delete')) {
                this.loadSession(session.session_id);
            }
        });
        
        return sessionDiv;
    }
    
    async loadSession(sessionId) {
        try {
            const response = await fetch(`/api/sessions/${sessionId}/history/`);
            const data = await response.json();
            
            if (data.success) {
                this.currentSessionId = sessionId;
                this.sessionId = sessionId;
                this.chatHistory = data.history || [];
                
                // 세션 목록에서 활성 상태 업데이트
                this.updateActiveSession(sessionId);
                
                // 채팅창 내용 복원
                this.renderChatHistory();
            }
        } catch (error) {
            console.error('세션 로드 오류:', error);
        }
    }
    
    updateActiveSession(sessionId) {
        // 모든 세션에서 active 클래스 제거
        document.querySelectorAll('.chat-session-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // 현재 세션에 active 클래스 추가
        const currentSession = document.querySelector(`[data-session-id="${sessionId}"]`);
        if (currentSession) {
            currentSession.classList.add('active');
        }
    }
    
    updateSessionTimestamp(sessionId) {
        // 현재 세션의 timestamp 업데이트
        const session = this.sessions.find(s => s.session_id === sessionId);
        if (session) {
            session.updated_at = new Date().toISOString();
            
            // 세션을 updated_at 순으로 재정렬 (최신순)
            this.sessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
            
            // 화면 업데이트
            this.renderSessions();
            this.updateActiveSession(sessionId);
        }
    }
    
    updateSessionTitle(sessionId, newTitle) {
        // 세션 제목 업데이트 (50자 이내로 제한)
        const session = this.sessions.find(s => s.session_id === sessionId);
        if (session) {
            session.title = newTitle.length > 50 ? newTitle.substring(0, 50) + "..." : newTitle;
            
            // 화면 업데이트
            this.renderSessions();
            this.updateActiveSession(sessionId);
        }
    }
    
    renderChatHistory() {
        this.chatMessages.innerHTML = '';
        
        // 시작 메시지 추가
        const currentTime = this.getCurrentTime();
        const startMessageHTML = `
            <div class="chat-start__container">
                <div class="chat-start__inside">
                    <div class="brand-name">JemBot Message</div>
                    <div class="chat-start__time">Today ${currentTime}</div>
                </div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', startMessageHTML);
        
        // 저장된 메시지들 복원
        this.chatHistory.forEach(msg => {
            if (msg.type === 'user') {
                this.addUserMessage(msg.content, msg.timestamp, false);
            } else if (msg.type === 'bot') {
                this.addBotMessage(msg.content, msg.timestamp, 'basic', false);
            }
        });
        
        this.scrollToBottom();
    }
    
    async startNewChat() {
        try {
            const response = await fetch('/api/sessions/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({
                    title: '새로운 대화'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('새 세션 생성 응답:', data);
            
            if (data.success) {
                this.currentSessionId = data.session.session_id;
                this.sessionId = data.session.session_id;
                this.chatHistory = [];
                
                // 세션을 로컬 목록에 추가
                const newSession = {
                    id: data.session.id,
                    session_id: data.session.session_id,
                    title: data.session.title,
                    created_at: data.session.created_at,
                    updated_at: data.session.created_at
                };
                this.sessions.unshift(newSession); // 목록 맨 앞에 추가
                
                // 화면 즉시 업데이트
                this.renderSessions();
                this.updateActiveSession(this.currentSessionId);
                
                // 채팅창 초기화
                this.initializeChatWindow();
                
            } else {
                console.error('세션 생성 실패:', data.error);
                alert('새 대화를 시작할 수 없습니다.');
            }
        } catch (error) {
            console.error('새 세션 생성 오류:', error);
            alert('서버 연결에 문제가 있습니다.');
        }
    }
    
    initializeChatWindow() {
        this.chatMessages.innerHTML = '';
        const currentTime = this.getCurrentTime();
        const startMessageHTML = `
            <div class="chat-start__container">
                <div class="chat-start__inside">
                    <div class="brand-name">JemBot Message</div>
                    <div class="chat-start__time">Today ${currentTime}</div>
                </div>
            </div>
            <div class="chat-bot">
                <div class="chat-bot__content">안녕하세요! 무엇을 도와드릴까요?</div>
                <div class="chat-bot__time">${currentTime}</div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', startMessageHTML);
        this.scrollToBottom();
    }
    
    async deleteSession(sessionId) {
        if (!confirm('이 대화를 삭제하시겠습니까?')) return;
        
        try {
            const response = await fetch(`/api/sessions/${sessionId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('세션 삭제 응답:', data);
            
            if (data.success) {
                // 세션 목록에서 제거
                this.sessions = this.sessions.filter(s => s.session_id !== sessionId);
                this.renderSessions();
                
                // 현재 세션이 삭제된 경우
                if (sessionId === this.currentSessionId) {
                    this.currentSessionId = null;
                    this.sessionId = '';
                    this.chatHistory = [];
                    
                    // 다른 세션이 있으면 첫 번째 세션 로드, 없으면 새 세션 시작
                    if (this.sessions.length > 0) {
                        this.loadSession(this.sessions[0].session_id);
                    } else {
                        this.startNewChat();
                    }
                }
            } else {
                console.error('세션 삭제 실패:', data.error);
                alert('대화를 삭제할 수 없습니다.');
            }
        } catch (error) {
            console.error('세션 삭제 오류:', error);
            alert('서버 연결에 문제가 있습니다.');
        }
    }
    
    setLevel(levelNumber) {
        const levelMap = {
            '1': 'basic',
            '2': 'intermediate', 
            '3': 'advanced'
        };
        
        this.currentLevel = levelMap[levelNumber] || 'basic';
        console.log('레벨 설정:', levelNumber, '→', this.currentLevel);
        
        // 해당 버튼 체크
        const buttonId = `btnradio${levelNumber}`;
        const button = document.getElementById(buttonId);
        if (button) {
            button.checked = true;
        }
    }
    
    updateLevel() {
        // 하위 호환성을 위해 유지
        console.log('현재 레벨:', this.currentLevel);
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isLoading) return;
        
        // 세션이 없으면 새로 생성
        if (!this.currentSessionId) {
            await this.startNewChat();
        }
        
        // 사용자 메시지 추가
        this.addUserMessage(message);
        this.chatInput.value = '';
        this.scrollToBottom();
        
        // 로딩 상태 시작
        this.isLoading = true;
        this.addLoadingMessage();
        this.scrollToBottom();
        
        try {
            // API 호출 전 로그
            console.log('API 호출 데이터:', {
                message: message,
                level: this.currentLevel,
                session_id: this.sessionId,
                chat_history: this.chatHistory
            });
            
            // API 호출
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({
                    message: message,
                    level: this.currentLevel,
                    session_id: this.sessionId,
                    chat_history: this.chatHistory
                })
            });
            
            const data = await response.json();
            
            // 로딩 메시지 제거
            this.removeLoadingMessage();
            
            if (data.success) {
                // 세션 ID 저장
                if (data.session_id) {
                    this.sessionId = data.session_id;
                    this.currentSessionId = data.session_id;
                }
                
                // 봇 응답 추가
                this.addBotMessage(data.bot_message, data.timestamp, data.level);
                
                // 대화 기록에 추가
                this.chatHistory.push({
                    type: 'user',
                    content: message,
                    timestamp: this.getCurrentTime()
                });
                this.chatHistory.push({
                    type: 'bot',
                    content: data.bot_message,
                    timestamp: data.timestamp,
                    level: data.level
                });
                
                // 세션 목록에서 현재 세션의 updated_at 시간 업데이트
                this.updateSessionTimestamp(this.currentSessionId);
                
                // 첫 번째 메시지인 경우 세션 제목 업데이트
                if (this.chatHistory.length === 2) { // user + bot = 2
                    this.updateSessionTitle(this.currentSessionId, message);
                }
            } else {
                // 에러 메시지 추가
                this.addBotMessage('죄송합니다. 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), this.getCurrentTime());
            }
            
        } catch (error) {
            console.error('Chat API Error:', error);
            this.removeLoadingMessage();
            this.addBotMessage('죄송합니다. 서버와의 연결에 문제가 발생했습니다.', this.getCurrentTime());
        }
        
        this.isLoading = false;
        this.scrollToBottom();
    }
    
    addUserMessage(message, time = null, saveToHistory = true) {
        const currentTime = time || this.getCurrentTime();
        const userMessageHTML = `
            <div class="chat-user">
                <div class="chat-user__time">${currentTime}</div>
                <div class="chat-user__content">${this.escapeHtml(message)}</div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', userMessageHTML);
        
        if (saveToHistory) {
            this.chatHistory.push({
                type: 'user',
                content: message,
                timestamp: currentTime
            });
        }
    }
    
    addBotMessage(message, timestamp, level = 'basic', saveToHistory = true) {
        const levelMap = {
            'basic': '초급',
            'intermediate': '중급',
            'advanced': '고급'
        };
        
        const levelText = levelMap[level] || '초급';
        const levelClass = level === 'intermediate' ? 'intermediate_answer__mark' : 
                          level === 'advanced' ? 'advanced_answer__mark' : 'beginner_answer__mark';
        
        const botMessageHTML = `
            <div class="chat-bot" id="${level}_answer">
                <div class="${levelClass}">${levelText}</div>
                <div class="chat-bot__content">${this.formatMessage(message)}</div>
                <div class="chat-bot__time">${timestamp}</div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', botMessageHTML);
        
        if (saveToHistory) {
            this.chatHistory.push({
                type: 'bot',
                content: message,
                timestamp: timestamp,
                level: level
            });
        }
    }
    
    addLoadingMessage() {
        const loadingHTML = `
            <div class="chat-bot loading-message" id="loading-message">
                <div class="chat-bot__content">
                    <div class="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
                <div class="chat-bot__time">${this.getCurrentTime()}</div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', loadingHTML);
    }
    
    removeLoadingMessage() {
        const loadingMessage = document.getElementById('loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }
    
    formatMessage(message) {
        // 줄바꿈을 <br> 태그로 변환
        return this.escapeHtml(message).replace(/\n/g, '<br>');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getCurrentTime() {
        const now = new Date();
        return now.getHours().toString().padStart(2, '0') + ':' + 
               now.getMinutes().toString().padStart(2, '0');
    }
    
    scrollToBottom() {
        // 스크롤을 맨 아래로 이동
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
}

// 전역 변수로 chatBot 인스턴스 생성
let chatBot;

// 페이지 로드 시 채팅봇 초기화
document.addEventListener('DOMContentLoaded', () => {
    chatBot = new ChatBot();
}); 