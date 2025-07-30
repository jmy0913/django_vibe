class ChatBot {
    constructor() {
        this.chatMessages = document.querySelector('.chat-messages');
        this.chatInput = document.querySelector('.chat-input__box input');
        this.sendButton = document.querySelector('.chat-search-button button');
        this.levelButtons = document.querySelectorAll('input[name="btnradio"]');
        
        this.currentLevel = 'basic';
        this.isLoading = false;
        this.sessionId = '';
        this.chatHistory = [];
        this.currentChatId = null;
        this.allChats = {};
        
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
        
        // 레벨 선택 이벤트
        this.levelButtons.forEach(button => {
            button.addEventListener('change', (e) => {
                console.log('레벨 버튼 클릭:', e.target.id);
                this.currentLevel = e.target.id.replace('btnradio', '');
                this.updateLevel();
            });
            
            // 라벨 클릭 이벤트도 추가
            const label = button.nextElementSibling;
            if (label) {
                label.addEventListener('click', (e) => {
                    console.log('라벨 클릭:', button.id);
                    button.checked = true;
                    this.currentLevel = button.id.replace('btnradio', '');
                    this.updateLevel();
                });
            }
        });
        
        // 새 채팅 버튼 이벤트
        const newChatButton = document.querySelector('.chat-add-button button');
        if (newChatButton) {
            newChatButton.addEventListener('click', () => this.startNewChat());
        }
        
        // 삭제 버튼 이벤트 등록
        this.setupDeleteButtons();
        
        // 초기 레벨 설정 (기본값: 초급)
        this.currentLevel = '1';
        
        // 초기 버튼 상태 설정
        const initialButton = document.getElementById('btnradio1');
        if (initialButton) {
            initialButton.checked = true;
        }
        
        this.updateLevel();
        
        // 페이지 로드 시 저장된 채팅 복원 또는 새 채팅 시작
        this.loadSavedChats();
    }
    
    loadSavedChats() {
        // localStorage에서 저장된 채팅들 불러오기
        const savedChats = localStorage.getItem('jembot_chats');
        if (savedChats) {
            this.allChats = JSON.parse(savedChats);
            
            // 대화목록에 저장된 채팅들 표시
            Object.keys(this.allChats).forEach(chatId => {
                const chat = this.allChats[chatId];
                this.addChatToList(chat.title, chat.lastTime, chatId);
            });
            
            // 마지막 채팅이 있으면 로드
            const lastChatId = localStorage.getItem('jembot_last_chat');
            if (lastChatId && this.allChats[lastChatId]) {
                this.loadChat(lastChatId);
            } else {
                // 새 채팅 시작
                this.startNewChat();
            }
        } else {
            // 저장된 채팅이 없으면 새 채팅 시작
            this.startNewChat();
        }
    }
    
    saveChats() {
        // localStorage에 채팅들 저장
        localStorage.setItem('jembot_chats', JSON.stringify(this.allChats));
        if (this.currentChatId) {
            localStorage.setItem('jembot_last_chat', this.currentChatId);
        }
    }
    
    saveCurrentChat() {
        if (!this.currentChatId) return;
        
        // 현재 채팅 정보 저장
        this.allChats[this.currentChatId] = {
            title: this.getChatTitle(),
            lastTime: this.getCurrentTime(),
            sessionId: this.sessionId,
            messages: this.chatHistory,
            startTime: this.getCurrentTime()
        };
        
        this.saveChats();
    }
    
    getChatTitle() {
        if (this.chatHistory.length === 0) return '새로운 대화';
        
        // 첫 번째 사용자 메시지를 제목으로 사용
        const firstUserMessage = this.chatHistory.find(msg => msg.type === 'user');
        if (firstUserMessage) {
            const shortMessage = firstUserMessage.content.length > 20 
                ? firstUserMessage.content.substring(0, 20) + '...' 
                : firstUserMessage.content;
            return shortMessage;
        }
        
        return '새로운 대화';
    }
    
    updateLevel() {
        const levelMap = {
            '1': 'basic',
            '2': 'intermediate', 
            '3': 'advanced'
        };
        const selectedLevel = levelMap[this.currentLevel] || 'basic';
        this.currentLevel = selectedLevel;
        console.log('레벨 변경됨:', this.currentLevel);
        
        // 모든 버튼의 checked 상태 해제
        this.levelButtons.forEach(button => {
            button.checked = false;
        });
        
        // 현재 선택된 버튼에 checked 속성 추가
        const selectedButtonId = this.currentLevel === 'basic' ? 'btnradio1' : 
                                this.currentLevel === 'intermediate' ? 'btnradio2' : 'btnradio3';
        const selectedButton = document.getElementById(selectedButtonId);
        if (selectedButton) {
            selectedButton.checked = true;
        }
    }
    
    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message || this.isLoading) return;
        
        // 첫 번째 메시지인 경우 새 채팅 시작
        if (!this.currentChatId) {
            this.startNewChat();
        }
        
        // 사용자 메시지 추가
        this.addUserMessage(message);
        this.chatInput.value = '';
        this.scrollToBottom();
        
        // 첫 번째 메시지인 경우 대화목록 제목 업데이트
        if (this.chatHistory.length === 0) {
            this.updateChatTitle(message);
        }
        
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
            const response = await fetch('/jembot/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
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
                }
                // 봇 응답 추가
                this.addBotMessage(data.bot_message, data.timestamp, data.level);
                
                // 대화 기록에 추가
                this.chatHistory.push({
                    type: 'user',
                    content: message,
                    time: this.getCurrentTime()
                });
                this.chatHistory.push({
                    type: 'bot',
                    content: data.bot_message,
                    time: data.timestamp,
                    level: data.level
                });
                
                // 현재 채팅 저장
                this.saveCurrentChat();
            } else {
                // 에러 메시지 추가
                this.addBotMessage('죄송합니다. 오류가 발생했습니다: ' + (data.error || '알 수 없는 오류'), data.timestamp || this.getCurrentTime());
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
                time: currentTime
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
                time: timestamp,
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
    
    startNewChat() {
        // 새 채팅 시작
        this.sessionId = '';
        this.currentChatId = this.generateChatId();
        this.chatHistory = [];
        
        // 기존 메시지들 제거 (시작 메시지 제외)
        const messages = this.chatMessages.querySelectorAll('.chat-bot:not(.chat-start__container), .chat-user');
        messages.forEach(msg => msg.remove());
        
        // 새 채팅 시작 메시지 추가
        const currentTime = this.getCurrentTime();
        const startMessageHTML = `
            <div class="chat-start__container">
                <div class="chat-start__inside">
                    <div class="brand-name">JemBot Message</div>
                    <div class="chat-start__time">Today ${currentTime}</div>
                </div>
            </div>
            <div class="chat-bot">
                <div class="chat-bot__content">안녕하세요 무엇을 도와드릴까요?</div>
                <div class="chat-bot__time">${currentTime}</div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', startMessageHTML);
        
        // 대화목록에 새 채팅 추가
        this.addChatToList('새로운 대화', currentTime);
        
        this.scrollToBottom();
    }
    
    generateChatId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    addChatToList(title, time, chatId = null) {
        const chatList = document.querySelector('.chat-list__item');
        const targetChatId = chatId || this.currentChatId;
        
        // 기존 "저장된 대화가 없습니다" 메시지 제거
        const emptyMessage = chatList.querySelector('.chat-list__empty');
        if (emptyMessage) {
            emptyMessage.remove();
        }
        
        const chatHTML = `
            <div class="chat-list__box" data-chat-id="${targetChatId}">
                <div class="chat-list__text" onclick="chatBot.loadChat('${targetChatId}')">
                    <div class="chat-list__title">${title}</div>
                    <div class="chat-list__time">${time}</div>
                </div>
                <div class="dropdown">
                    <button class="btn btn-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false"></button>
                    <ul class="dropdown-menu">
                        <li><button class="dropdown-item" type="button">Share</button></li>
                        <li><button class="dropdown-item" type="button">Rename</button></li>
                        <li><button class="dropdown-item delete-chat-btn" type="button" data-chat-id="${targetChatId}">Delete</button></li>
                    </ul>
                </div>
            </div>
        `;
        
        chatList.insertAdjacentHTML('afterbegin', chatHTML);
        this.setupDeleteButtons();
    }
    
    setupDeleteButtons() {
        // 삭제 버튼 이벤트 등록
        const deleteButtons = document.querySelectorAll('.delete-chat-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const chatId = button.getAttribute('data-chat-id');
                this.deleteChat(chatId);
            });
        });
    }
    
    deleteChat(chatId) {
        // 대화목록에서 제거
        const chatElement = document.querySelector(`[data-chat-id="${chatId}"]`);
        if (chatElement) {
            chatElement.remove();
        }
        
        // allChats에서 제거
        delete this.allChats[chatId];
        this.saveChats();
        
        // 대화목록이 비어있으면 "저장된 대화가 없습니다" 메시지 표시
        const chatList = document.querySelector('.chat-list__item');
        const remainingChats = chatList.querySelectorAll('.chat-list__box');
        if (remainingChats.length === 0) {
            chatList.innerHTML = '<div class="chat-list__empty">저장된 대화가 없습니다.</div>';
        }
        
        // 현재 채팅이 삭제된 경우 새 채팅 시작
        if (chatId === this.currentChatId) {
            this.startNewChat();
        }
    }
    
    updateChatTitle(message) {
        // 대화목록의 제목을 첫 번째 메시지로 업데이트
        const chatElement = document.querySelector(`[data-chat-id="${this.currentChatId}"]`);
        if (chatElement) {
            const titleElement = chatElement.querySelector('.chat-list__title');
            if (titleElement) {
                // 메시지가 길면 잘라서 표시
                const shortMessage = message.length > 20 ? message.substring(0, 20) + '...' : message;
                titleElement.textContent = shortMessage;
            }
        }
    }
    
    loadChat(chatId) {
        if (!this.allChats[chatId]) return;
        
        const chat = this.allChats[chatId];
        this.currentChatId = chatId;
        this.sessionId = chat.sessionId || '';
        this.chatHistory = chat.messages || [];
        
        // 채팅창 내용 복원
        this.chatMessages.innerHTML = '';
        
        // 시작 메시지 추가
        const startMessageHTML = `
            <div class="chat-start__container">
                <div class="chat-start__inside">
                    <div class="brand-name">JemBot Message</div>
                    <div class="chat-start__time">Today ${chat.startTime}</div>
                </div>
            </div>
        `;
        this.chatMessages.insertAdjacentHTML('beforeend', startMessageHTML);
        
        // 저장된 메시지들 복원
        this.chatHistory.forEach(msg => {
            if (msg.type === 'user') {
                this.addUserMessage(msg.content, msg.time, false);
            } else if (msg.type === 'bot') {
                this.addBotMessage(msg.content, msg.time, msg.level, false);
            }
        });
        
        this.scrollToBottom();
    }
}

// 전역 변수로 chatBot 인스턴스 생성
let chatBot;

// 페이지 로드 시 채팅봇 초기화
document.addEventListener('DOMContentLoaded', () => {
    chatBot = new ChatBot();
}); 