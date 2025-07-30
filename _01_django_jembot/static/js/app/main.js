// 뉴스 및 주식 관리 클래스
class NewsStockManager {
    constructor() {
        this.newsContainer = document.querySelector('#news-container');
        this.stockContainer = document.querySelector('#stock-container');
        this.searchInput = document.querySelector('#search-input');
        this.searchButton = document.querySelector('#search-button');
        this.newsButton = document.querySelector('#news-button');
        this.stockButton = document.querySelector('#stock-button');
        
        this.currentMode = 'news'; // 'news' 또는 'stock'
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        // 요소 찾기 확인 로그
        console.log('NewsStockManager 초기화:');
        console.log('- 검색 입력:', this.searchInput);
        console.log('- 검색 버튼:', this.searchButton);
        console.log('- 뉴스 버튼:', this.newsButton);
        console.log('- 주식 버튼:', this.stockButton);
        console.log('- CSRF 토큰:', this.csrfToken);
        
        this.init();
    }
    
    init() {
        // 검색 버튼 클릭 이벤트
        if (this.searchButton) {
            this.searchButton.addEventListener('click', () => this.handleSearch());
        }
        
        // 엔터키 검색 이벤트
        if (this.searchInput) {
            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleSearch();
                }
            });
        }
        
        // 초기 플레이스홀더 설정
        this.updateSearchPlaceholder();
        
        // 초기 뉴스 로드 (기본 키워드로)
        this.loadDefaultNews();
    }
    
    updateSearchPlaceholder() {
        if (this.searchInput) {
            const newPlaceholder = this.currentMode === 'news' ? '뉴스 검색' : '주식 검색 (예: 삼성전자)';
            this.searchInput.placeholder = newPlaceholder;
            console.log('플레이스홀더 업데이트:', this.currentMode, '→', newPlaceholder);
        } else {
            console.error('검색 입력 필드를 찾을 수 없습니다');
        }
    }
    
    async handleSearch() {
        const query = this.searchInput.value.trim();
        console.log('검색 시작:', query, '모드:', this.currentMode);
        
        if (!query) {
            alert('검색어를 입력해주세요.');
            return;
        }
        
        if (this.currentMode === 'news') {
            console.log('뉴스 검색 실행');
            await this.searchNews(query);
        } else {
            console.log('주식 검색 실행');
            await this.searchStock(query);
        }
    }
    
    async loadDefaultNews() {
        // 기본 경제 뉴스 로드
        await this.searchNews('경제');
    }
    
    async searchNews(query) {
        try {
            this.showLoading(this.newsContainer, '뉴스를 검색중입니다...');
            
            const response = await fetch('/api/news/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.renderNews(data.news);
            } else {
                this.showError(this.newsContainer, data.error || '뉴스 검색에 실패했습니다.');
            }
        } catch (error) {
            console.error('뉴스 검색 오류:', error);
            this.showError(this.newsContainer, '서버 연결에 문제가 있습니다.');
        }
    }
    
    async searchStock(query) {
        try {
            this.showLoading(this.stockContainer, '주식 정보를 검색중입니다...');
            
            const response = await fetch('/api/stock/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({ query: query, period: '1m' })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.renderStock(data);
            } else {
                this.showError(this.stockContainer, data.error || '주식 검색에 실패했습니다.');
            }
        } catch (error) {
            console.error('주식 검색 오류:', error);
            this.showError(this.stockContainer, '서버 연결에 문제가 있습니다.');
        }
    }
    
    renderNews(newsList) {
        this.newsContainer.innerHTML = '';
        
        newsList.forEach(news => {
            const newsBox = document.createElement('div');
            newsBox.className = 'news-box';
            
            newsBox.innerHTML = `
                <div class="news-box__top">
                    <div class="news-label__mark">${news.press}</div>
                    <div class="news-label__time">${news.time}</div>
                </div>
                <div class="news-title">${news.title}</div>
                <div class="news-content">${news.content}</div>
                ${news.link !== '#' ? `<a href="${news.link}" target="_blank" class="news-link">원문 보기</a>` : ''}
            `;
            
            this.newsContainer.appendChild(newsBox);
        });
    }
    
    renderStock(stockData) {
        const isPositive = stockData.priceChange.startsWith('+');
        const changeClass = isPositive ? 'positive' : 'negative';
        
        // placeholder 숨기기
        const placeholder = this.stockContainer.querySelector('.stock-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        this.stockContainer.innerHTML = `
            <div class="stock-box">
                <div class="stock-header">
                    <div class="stock-name">${stockData.companyName}</div>
                    <div class="stock-code">${stockData.code}</div>
                </div>
                <div class="stock-price-section">
                    <div class="current-price">₩ ${stockData.latestPrice}</div>
                    <div class="price-change ${changeClass}">${stockData.priceChange} (${stockData.changePercent}%)</div>
                    <div class="update-time">${new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })} KST</div>
                </div>
                <div class="stock-chart">
                    <canvas id="stockChart" width="300" height="100"></canvas>
                </div>
                <div class="stock-details">
                    <div class="detail-row">
                        <div class="detail-item">
                            <span class="label">시가총액</span>
                            <span class="value">${stockData.marketCap}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">거래량</span>
                            <span class="value">${stockData.volume}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-item">
                            <span class="label">52주 최고</span>
                            <span class="value">${stockData.fiftyTwoWeekHigh}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">52주 최저</span>
                            <span class="value">${stockData.fiftyTwoWeekLow}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-item">
                            <span class="label">${stockData.per_label}</span>
                            <span class="value">${stockData.per_value}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">${stockData.pbr_label}</span>
                            <span class="value">${stockData.pbr_value}</span>
                        </div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-item">
                            <span class="label">당일 최고가</span>
                            <span class="value">${stockData.dayHigh}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">당일 최저가</span>
                            <span class="value">${stockData.dayLow}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 차트 업데이트
        this.updateStockChart(stockData.chartData);
    }
    
    updateStockChart(chartData) {
        // 기존 차트 제거
        const existingChart = Chart.getChart('stockChart');
        if (existingChart) {
            existingChart.destroy();
        }
        
        // 새 차트 생성
        setTimeout(() => {
            const ctx = document.getElementById('stockChart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: '주가',
                            data: chartData.data,
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0,123,255,0.1)',
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { 
                            x: { display: true }, 
                            y: { display: true } 
                        }
                    }
                });
            }
        }, 100);
    }
    
    showLoading(container, message) {
        // placeholder 숨기기 (주식용)
        const placeholder = container.querySelector('.stock-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        container.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-message">${message}</div>
            </div>
        `;
    }
    
    showError(container, message) {
        // placeholder 숨기기 (주식용)
        const placeholder = container.querySelector('.stock-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        container.innerHTML = `
            <div class="error-container">
                <div class="error-message">${message}</div>
            </div>
        `;
    }
}

const sideButtonHandler = (newsStockManager) => {
    const $buttons = document.querySelectorAll('#news-button, #stock-button');
    const $news_container = document.querySelector('#news-container');
    const $stock_container = document.querySelector('#stock-container');

    const $newsButton = document.querySelector('#news-button');
    if ($newsButton) {
        $newsButton.classList.add('active');
    }

    $buttons.forEach(button => {
            button.addEventListener('click', function () {
            console.log(`${this.textContent} 버튼 클릭`);

            $buttons.forEach(btn => {
                btn.classList.remove('active');
            });

            this.classList.add('active');

            if (this.id === 'news-button') {
                $news_container.style.display = 'block';
                $stock_container.style.display = 'none';
                newsStockManager.currentMode = 'news';
                newsStockManager.updateSearchPlaceholder();
            } else if (this.id === 'stock-button') {
                $stock_container.style.display = 'block';
                $news_container.style.display = 'none';
                newsStockManager.currentMode = 'stock';
                newsStockManager.updateSearchPlaceholder();
            }
        });
    });
};

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    // 뉴스/주식 매니저 초기화
    const newsStockManager = new NewsStockManager();
    
    // 사이드 버튼 핸들러 초기화 (매니저 인스턴스 전달)
    sideButtonHandler(newsStockManager);
});
  