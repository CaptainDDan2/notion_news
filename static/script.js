// 반도체 뉴스 대시보드 JavaScript

// 간역 변수
let currentSection = 'dashboard';
let searchTimeout;
let isLoading = false;
let currentArticleId = null;

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 앱 초기화
function initializeApp() {
    console.log('반도체 뉴스 대시보드 초기화...');
    
    // 이벤트 리스너 설정
    setupEventListeners();
    
    // 검색 입력 이벤트
    setupSearchInput();
    
    // 모바일 사이드바 설정
    setupMobileSidebar();
    
    // 초기 데이터 로드
    loadInitialData();
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 네비게이션 클릭
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.dataset.section;
            switchSection(section);
        });
    });
    
    // 모달 외부 클릭시 닫기
    const modal = document.getElementById('article-modal');
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // 키보드 이벤트
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// 검색 입력 설정
function setupSearchInput() {
    const searchInput = document.getElementById('search-input');
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length > 0) {
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 500); // 500ms 지연으로 디바운스
        } else {
            // 검색어가 없으면 대시보드로 돌아가기
            if (currentSection === 'search') {
                switchSection('dashboard');
            }
        }
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = this.value.trim();
            if (query.length > 0) {
                performSearch(query);
            }
        }
    });
}

// 섹션 전환
function switchSection(sectionName) {
    if (isLoading) return;
    
    // 모든 섹션 숨기기
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // 모든 네비게이션 아이템 비활성화
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 선택된 섹션 활성화
    const targetSection = document.getElementById(`${sectionName}-section`);
    const targetNavItem = document.querySelector(`[data-section="${sectionName}"]`);
    
    if (targetSection && targetNavItem) {
        targetSection.classList.add('active');
        targetNavItem.classList.add('active');
        currentSection = sectionName;
        
        // 페이지 제목 업데이트
        updatePageTitle(sectionName);
        
        // 섹션별 데이터 로드
        loadSectionData(sectionName);
    }
}

// 페이지 제목 업데이트
function updatePageTitle(sectionName) {
    const titles = {
        'dashboard': '반도체 뉴스 대시보드',
        'priority': '우선순위 높은 뉴스',
        'recent': '최신 뉴스',
        'trends': '현재 트렌드',
        'search': '검색 결과'
    };
    
    const titleElement = document.getElementById('page-title');
    titleElement.textContent = titles[sectionName] || '반도체 뉴스 대시보드';
}

// 섹션별 데이터 로드
function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'priority':
            loadPriorityArticles();
            break;
        case 'recent':
            loadRecentArticles();
            break;
        case 'personalized':
            loadPersonalizedArticles();
            break;
        case 'bookmarks':
            loadBookmarkedArticles();
            break;
        case 'trends':
            loadTrends();
            break;
        case 'dashboard':
            // 대시보드는 이미 서버에서 렌더링됨
            break;
    }
}

// 우선순위 기사 로드
async function loadPriorityArticles() {
    showLoading();
    
    try {
        const response = await fetch('/api/articles?sort=priority&limit=10');
        const data = await response.json();
        
        if (data.success) {
            displayArticles(data.articles, 'priority-articles-container');
        } else {
            showToast('우선순위 기사를 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('우선순위 기사 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

// 최신 기사 로드
async function loadRecentArticles() {
    showLoading();
    
    try {
        const response = await fetch('/api/articles?sort=recent&limit=10');
        const data = await response.json();
        
        if (data.success) {
            displayArticles(data.articles, 'recent-articles-container');
        } else {
            showToast('최신 기사를 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('최신 기사 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

// 개인화된 기사 로드
async function loadPersonalizedArticles() {
    showLoading();
    
    try {
        const response = await fetch('/api/articles/personalized?sort=priority&limit=10');
        const data = await response.json();
        
        if (data.success) {
            displayArticles(data.articles, 'personalized-articles-container', '개인화된 추천 기사');
        } else {
            showToast('개인화된 기사를 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('개인화된 기사 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

// 북마크된 기사 로드
async function loadBookmarkedArticles() {
    showLoading();
    
    try {
        const response = await fetch('/api/bookmarks?user_id=default&limit=50');
        const data = await response.json();
        
        if (data.success) {
            displayBookmarks(data.bookmarks, 'bookmarks-container');
        } else {
            showToast('북마크된 기사를 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('북마크 기사 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

// 트렌드 로드
async function loadTrends() {
    showLoading();
    
    try {
        const [trendsResponse, statsResponse] = await Promise.all([
            fetch('/api/trends'),
            fetch('/api/stats')
        ]);
        
        const trendsData = await trendsResponse.json();
        const statsData = await statsResponse.json();
        
        if (trendsData.success && statsData.success) {
            displayTrends(trendsData.trends, statsData.stats);
        } else {
            showToast('트렌드 데이터를 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('트렌드 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

// 검색 수행
async function performSearch(query) {
    if (currentSection !== 'search') {
        switchSection('search');
    }
    
    showLoading();
    
    try {
        const response = await fetch(`/api/articles?search=${encodeURIComponent(query)}&limit=30`);
        const data = await response.json();
        
        if (data.success) {
            displayArticles(data.articles, 'search-results-container', `"${query}" 검색 결과 (${data.articles.length}개)`);
        } else {
            showToast('검색에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('검색 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

// 기사 목록 표시
function displayArticles(articles, containerId, title = '') {
    const container = document.getElementById(containerId);
    
    if (!articles || articles.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #9b9a97;">
                <i class="fas fa-newspaper" style="font-size: 48px; margin-bottom: 16px;"></i>
                <p>표시할 기사가 없습니다.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    if (title) {
        html += `<div style="margin-bottom: 24px;"><h3>${title}</h3></div>`;
    }
    
    articles.forEach(article => {
        const priorityClass = getPriorityClass(article.priority_score);
        const formattedDate = formatDate(article.published_date || article.crawled_at);
        
        html += `
            <div class="article-card" onclick="showArticleDetail(${article.id})">
                <div class="article-header">
                    <span class="priority-badge ${priorityClass}">
                        ${article.priority_score.toFixed(1)}
                    </span>
                    <span class="source">${escapeHtml(article.source)}</span>
                </div>
                <h4>${escapeHtml(article.title)}</h4>
                <p class="summary">${escapeHtml(article.summary || article.content.substring(0, 150))}...</p>
                <div class="article-footer">
                    <span class="date">${formattedDate}</span>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 트렌드 표시
function displayTrends(trends, stats) {
    const container = document.getElementById('trends-container');
    
    let html = `
        <div class="overview-grid">
            <div class="overview-card">
                <h3>🔥 인기 키워드</h3>
                <div class="trends-keywords">
    `;
    
    if (trends.top_trends && trends.top_trends.length > 0) {
        trends.top_trends.forEach(([keyword, count]) => {
            const size = Math.min(16 + count * 2, 24);
            html += `
                <span class="trend-keyword" style="font-size: ${size}px; margin: 4px 8px; padding: 4px 8px; background-color: rgba(35, 131, 226, 0.1); border-radius: 4px; display: inline-block;">
                    ${escapeHtml(keyword)} (${count})
                </span>
            `;
        });
    } else {
        html += '<p style="color: #9b9a97;">트렌드 키워드가 없습니다.</p>';
    }
    
    html += `
                </div>
            </div>
            <div class="overview-card">
                <h3>📊 소스별 통계</h3>
                <div class="source-stats">
    `;
    
    if (stats.source_stats && stats.source_stats.length > 0) {
        stats.source_stats.forEach(stat => {
            const percentage = stats.total_articles > 0 ? (stat.count / stats.total_articles * 100).toFixed(1) : 0;
            html += `
                <div class="stat-item" style="display: flex; justify-content: space-between; align-items: center; margin: 8px 0; padding: 8px; background-color: #f7f7f5; border-radius: 4px;">
                    <span>${escapeHtml(stat.source)}</span>
                    <span>${stat.count}개 (${percentage}%)</span>
                </div>
            `;
        });
    } else {
        html += '<p style="color: #9b9a97;">통계 데이터가 없습니다.</p>';
    }
    
    html += `
                </div>
            </div>
        </div>
        
        <div class="overview-card" style="margin-top: 32px;">
            <h3>📈 최근 7일간 기사 수</h3>
            <div class="daily-stats" style="display: flex; gap: 8px; margin-top: 16px;">
    `;
    
    if (stats.daily_stats && stats.daily_stats.length > 0) {
        const maxCount = Math.max(...stats.daily_stats.map(s => s.count));
        stats.daily_stats.forEach(stat => {
            const height = maxCount > 0 ? (stat.count / maxCount * 100) : 0;
            html += `
                <div class="daily-stat" style="flex: 1; text-align: center;">
                    <div style="height: 100px; display: flex; align-items: end; margin-bottom: 8px;">
                        <div style="width: 100%; background-color: #2383e2; height: ${height}%; border-radius: 4px 4px 0 0;"></div>
                    </div>
                    <div style="font-size: 12px; color: #9b9a97;">${stat.date.slice(5)}</div>
                    <div style="font-size: 14px; font-weight: 600;">${stat.count}</div>
                </div>
            `;
        });
    }
    
    html += '</div></div>';
    
    container.innerHTML = html;
}

// 기사 상세 모달 표시
async function showArticleDetail(articleId) {
    showLoading();
    currentArticleId = articleId;
    
    try {
        const response = await fetch(`/api/article/${articleId}`);
        const data = await response.json();
        
        if (data.success) {
            const article = data.article;
            
            document.getElementById('modal-title').textContent = article.title;
            document.getElementById('modal-source').textContent = article.source;
            document.getElementById('modal-date').textContent = formatDate(article.published_date || article.crawled_at);
            document.getElementById('modal-priority').textContent = article.priority_score.toFixed(1);
            document.getElementById('modal-priority').className = `priority-badge ${getPriorityClass(article.priority_score)}`;
            document.getElementById('modal-summary').textContent = article.summary || '요약이 없습니다.';
            document.getElementById('modal-content').textContent = article.content;
            document.getElementById('modal-link').href = article.url;
            
            document.getElementById('article-modal').style.display = 'block';
        } else {
            showToast('기사 정보를 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('기사 상세 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}


// 모달 닫기
function closeModal() {
    document.getElementById('article-modal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

// 수동 크롤링
async function manualCrawl() {
    const button = document.querySelector('.crawl-btn');
    const originalText = button.innerHTML;
    
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 업데이트 중...';
    
    try {
        const response = await fetch('/api/crawl', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            
            // 통계 업데이트
            updateStats();
            
            // 현재 섹션 새로고침
            if (currentSection !== 'dashboard') {
                loadSectionData(currentSection);
            } else {
                // 대시보드는 페이지 새로고침
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showToast('뉴스 업데이트에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('수동 크롤링 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = originalText;
    }
}

// 통계 업데이트
async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('total-articles').textContent = data.stats.total_articles;
            document.getElementById('today-articles').textContent = data.stats.today_articles;
        }
    } catch (error) {
        console.error('통계 업데이트 오류:', error);
    }
}

// 초기 데이터 로드
function loadInitialData() {
    // 통계 업데이트
    updateStats();
}

// 유틸리티 함수들
function getPriorityClass(score) {
    if (score >= 9) return 'priority-10';
    if (score >= 7) return 'priority-8';
    if (score >= 5) return 'priority-6';
    return 'priority-4';
}

function formatDate(dateString) {
    if (!dateString) return '방금 전';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return '방금 전';
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    isLoading = true;
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    isLoading = false;
    document.getElementById('loading').style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 북마크 관련 함수들
function displayBookmarks(bookmarks, containerId) {
    const container = document.getElementById(containerId);
    
    if (!bookmarks || bookmarks.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #9b9a97;">
                <i class="fas fa-bookmark" style="font-size: 48px; margin-bottom: 16px;"></i>
                <p>북마크된 기사가 없습니다.</p>
                <p style="font-size: 14px; margin-top: 8px;">관심 있는 기사를 북마크해보세요.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    bookmarks.forEach(article => {
        const priorityClass = getPriorityClass(article.priority_score);
        const formattedDate = formatDate(article.published_date || article.crawled_at);
        const bookmarkDate = formatDate(article.bookmark_info.bookmarked_at);
        
        html += `
            <div class="article-card bookmark-card" onclick="showArticleDetail(${article.id})">
                <div class="article-header">
                    <span class="priority-badge ${priorityClass}">
                        ${article.priority_score.toFixed(1)}
                    </span>
                    <div class="bookmark-info">
                        <span class="source">${escapeHtml(article.source)}</span>
                        <span class="bookmark-date">북마크: ${bookmarkDate}</span>
                    </div>
                </div>
                <h4>${escapeHtml(article.title)}</h4>
                <p class="summary">${escapeHtml(article.summary || article.content.substring(0, 150))}...</p>
                ${article.bookmark_info.notes ? 
                    `<div class="bookmark-notes">
                        <i class="fas fa-sticky-note"></i>
                        ${escapeHtml(article.bookmark_info.notes)}
                    </div>` : ''
                }
                <div class="article-footer">
                    <span class="date">${formattedDate}</span>
                    <button onclick="event.stopPropagation(); removeBookmarkFromList(${article.id})" class="remove-bookmark-btn">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

async function toggleBookmark() {
    if (!currentArticleId) return;
    
    const bookmarkBtn = document.getElementById('bookmark-btn');
    const isBookmarked = bookmarkBtn.classList.contains('bookmarked');
    
    try {
        if (isBookmarked) {
            // 북마크 제거
            const response = await fetch(`/api/bookmarks/${currentArticleId}?user_id=default`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                bookmarkBtn.classList.remove('bookmarked');
                bookmarkBtn.innerHTML = '<i class="far fa-bookmark"></i> 북마크';
                showToast('북마크에서 제거되었습니다.', 'success');
            } else {
                showToast(data.error || '북마크 제거에 실패했습니다.', 'error');
            }
        } else {
            // 북마크 추가
            const response = await fetch('/api/bookmarks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'default',
                    article_id: currentArticleId,
                    notes: ''
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                bookmarkBtn.classList.add('bookmarked');
                bookmarkBtn.innerHTML = '<i class="fas fa-bookmark"></i> 북마크됨';
                showToast('북마크에 추가되었습니다.', 'success');
            } else {
                showToast(data.error || '북마크 추가에 실패했습니다.', 'error');
            }
        }
    } catch (error) {
        console.error('북마크 처리 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    }
}

async function updateBookmarkButton(articleId) {
    try {
        const response = await fetch(`/api/bookmarks/${articleId}/check?user_id=default`);
        const data = await response.json();
        
        const bookmarkBtn = document.getElementById('bookmark-btn');
        
        if (data.success && data.bookmarked) {
            bookmarkBtn.classList.add('bookmarked');
            bookmarkBtn.innerHTML = '<i class="fas fa-bookmark"></i> 북마크됨';
        } else {
            bookmarkBtn.classList.remove('bookmarked');
            bookmarkBtn.innerHTML = '<i class="far fa-bookmark"></i> 북마크';
        }
    } catch (error) {
        console.error('북마크 상태 확인 오류:', error);
    }
}

async function removeBookmarkFromList(articleId) {
    if (!confirm('이 기사를 북마크에서 제거하시겠습니까?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bookmarks/${articleId}?user_id=default`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('북마크에서 제거되었습니다.', 'success');
            // 북마크 목록 새로고침
            loadBookmarkedArticles();
        } else {
            showToast(data.error || '북마크 제거에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('북마크 제거 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    }
}

// 모바일 사이드바 관련 함수들
function setupMobileSidebar() {
    // 사이드바 오버레이 생성
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    overlay.addEventListener('click', closeMobileSidebar);
    document.body.appendChild(overlay);
    
    // 헤더 햄버거 메뉴 클릭 이벤트
    const header = document.querySelector('.main-header');
    header.addEventListener('click', function(e) {
        // 햄버거 메뉴 영역 클릭 감지 (왼쪽 50px)
        if (e.clientX < 50 && window.innerWidth <= 768) {
            toggleMobileSidebar();
        }
    });
    
    // 윈도우 크기 변경 시 사이드바 상태 리셋
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeMobileSidebar();
        }
    });
    
    // 네비게이션 아이템 클릭 시 모바일에서 사이드바 닫기
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeMobileSidebar();
            }
        });
    });
}

function toggleMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebar.classList.contains('open')) {
        closeMobileSidebar();
    } else {
        openMobileSidebar();
    }
}

function openMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    sidebar.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
}

function closeMobileSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// 스와이프 제스처 지원 (모바일)
let startX = 0;
let currentX = 0;
let isSwipeStart = false;

function setupSwipeGestures() {
    // 터치 이벤트 리스너
    document.addEventListener('touchstart', function(e) {
        if (window.innerWidth <= 768) {
            startX = e.touches[0].clientX;
            isSwipeStart = true;
        }
    });
    
    document.addEventListener('touchmove', function(e) {
        if (!isSwipeStart || window.innerWidth > 768) return;
        
        currentX = e.touches[0].clientX;
        const diff = currentX - startX;
        
        // 왼쪽에서 오른쪽으로 스와이프 (사이드바 열기)
        if (startX < 50 && diff > 50) {
            openMobileSidebar();
            isSwipeStart = false;
        }
        // 오른쪽에서 왼쪽으로 스와이프 (사이드바 닫기)
        else if (startX > 280 && diff < -50) {
            closeMobileSidebar();
            isSwipeStart = false;
        }
    });
    
    document.addEventListener('touchend', function() {
        isSwipeStart = false;
    });
}

// 페이지 로드 후 스와이프 제스처 설정
setTimeout(setupSwipeGestures, 100);

// 댓글 로드
async function loadComments(articleId) {
    // 댓글 기능이 비활성화되었습니다
    return;
}

// 댓글 작성
async function submitComment() {
    // 댓글 기능이 제거되었습니다
    showToast('댓글 기능은 현재 비활성화되어 있습니다.', 'info');
    return;
}

// 댓글 좋아요
async function likeComment(commentId) {
    // 댓글 기능 비활성화됨
    showToast('댓글 기능은 현재 비활성화되어 있습니다.', 'info');
    return;
}

// 공유 버튼

// 시간 차이 계산
function getTimeDifference(date) {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    if (days < 7) return `${days}일 전`;
    
    return date.toLocaleDateString('ko-KR');
}

// 관리자 뉴스 추가
async function submitAdminNews() {
    const title = document.getElementById('admin-title').value.trim();
    const content = document.getElementById('admin-content').value.trim();
    const source = document.getElementById('admin-source').value.trim() || '직접 입력';
    
    if (!title || !content) {
        showToast('제목과 내용을 모두 입력해주세요.', 'info');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/admin/news', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                content: content,
                source: source
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast('뉴스가 추가되었습니다.', 'success');
            
            // 폼 초기화
            document.getElementById('admin-title').value = '';
            document.getElementById('admin-content').value = '';
            document.getElementById('admin-source').value = '';
            
            // 대시보드 새로고침
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('뉴스 추가에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('관리자 뉴스 추가 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}


// 공유 통계 표시 (비활성화)
async function displayShareStats(articleId) {
    // 공유 기능이 제거되어 비활성화됨
    return;
}
