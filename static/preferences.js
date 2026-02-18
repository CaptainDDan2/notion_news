// 설정 페이지 JavaScript

let userPreferences = {
    interested_keywords: [],
    blocked_keywords: [],
    preferred_sources: [],
    min_priority_score: 0.0,
    max_articles_per_page: 20,
    notification_enabled: true,
    notification_priority_threshold: 7.0
};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializePreferences();
    setupEventListeners();
});

function initializePreferences() {
    loadUserPreferences();
    setupRangeSliders();
}

async function loadUserPreferences() {
    showLoading();
    
    try {
        const response = await fetch('/api/preferences');
        const data = await response.json();
        
        if (data.success) {
            userPreferences = data.preferences;
            populateForm();
        } else {
            showToast('설정을 불러오는데 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('설정 로드 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

function populateForm() {
    // 관심 키워드 표시
    displayKeywords('interest-keywords-list', userPreferences.interested_keywords, 'interest');
    
    // 차단 키워드 표시
    displayKeywords('block-keywords-list', userPreferences.blocked_keywords, 'block');
    
    // 선호 소스 체크박스 설정
    const sourceCheckboxes = document.querySelectorAll('input[name="source"]');
    sourceCheckboxes.forEach(checkbox => {
        checkbox.checked = userPreferences.preferred_sources.includes(checkbox.value);
    });
    
    // 필터 설정
    document.getElementById('min-priority').value = userPreferences.min_priority_score;
    document.getElementById('min-priority-value').textContent = userPreferences.min_priority_score.toFixed(1);
    
    document.getElementById('max-articles').value = userPreferences.max_articles_per_page;
    
    // 알림 설정
    document.getElementById('notifications-enabled').checked = userPreferences.notification_enabled;
    document.getElementById('notification-threshold').value = userPreferences.notification_priority_threshold;
    document.getElementById('notification-threshold-value').textContent = userPreferences.notification_priority_threshold.toFixed(1);
}

function displayKeywords(containerId, keywords, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    keywords.forEach(keyword => {
        const keywordTag = document.createElement('div');
        keywordTag.className = 'keyword-tag';
        keywordTag.innerHTML = `
            <span>${escapeHtml(keyword)}</span>
            <button type="button" onclick="removeKeyword('${type}', '${escapeHtml(keyword)}')" class="remove-keyword">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(keywordTag);
    });
}

function setupEventListeners() {
    // 키워드 입력 Enter 키 처리
    document.getElementById('interest-keyword-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addInterestKeyword();
        }
    });
    
    document.getElementById('block-keyword-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addBlockKeyword();
        }
    });
    
    // 폼 제출 처리
    document.getElementById('preferences-form').addEventListener('submit', function(e) {
        e.preventDefault();
        savePreferences();
    });
}

function setupRangeSliders() {
    const minPrioritySlider = document.getElementById('min-priority');
    const notificationThresholdSlider = document.getElementById('notification-threshold');
    
    minPrioritySlider.addEventListener('input', function() {
        document.getElementById('min-priority-value').textContent = parseFloat(this.value).toFixed(1);
    });
    
    notificationThresholdSlider.addEventListener('input', function() {
        document.getElementById('notification-threshold-value').textContent = parseFloat(this.value).toFixed(1);
    });
}

function addInterestKeyword() {
    const input = document.getElementById('interest-keyword-input');
    const keyword = input.value.trim();
    
    if (keyword && !userPreferences.interested_keywords.includes(keyword)) {
        userPreferences.interested_keywords.push(keyword);
        displayKeywords('interest-keywords-list', userPreferences.interested_keywords, 'interest');
        input.value = '';
    }
}

function addBlockKeyword() {
    const input = document.getElementById('block-keyword-input');
    const keyword = input.value.trim();
    
    if (keyword && !userPreferences.blocked_keywords.includes(keyword)) {
        userPreferences.blocked_keywords.push(keyword);
        displayKeywords('block-keywords-list', userPreferences.blocked_keywords, 'block');
        input.value = '';
    }
}

function removeKeyword(type, keyword) {
    if (type === 'interest') {
        const index = userPreferences.interested_keywords.indexOf(keyword);
        if (index > -1) {
            userPreferences.interested_keywords.splice(index, 1);
            displayKeywords('interest-keywords-list', userPreferences.interested_keywords, 'interest');
        }
    } else if (type === 'block') {
        const index = userPreferences.blocked_keywords.indexOf(keyword);
        if (index > -1) {
            userPreferences.blocked_keywords.splice(index, 1);
            displayKeywords('block-keywords-list', userPreferences.blocked_keywords, 'block');
        }
    }
}

async function savePreferences() {
    showLoading();
    
    try {
        // 폼 데이터 수집
        const formData = collectFormData();
        
        const response = await fetch('/api/preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: 'default',
                preferences: formData
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            userPreferences = data.preferences;
            showToast('설정이 저장되었습니다!', 'success');
        } else {
            showToast(data.error || '설정 저장에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('설정 저장 오류:', error);
        showToast('네트워크 오류가 발생했습니다.', 'error');
    } finally {
        hideLoading();
    }
}

function collectFormData() {
    // 선호 소스 수집
    const selectedSources = [];
    const sourceCheckboxes = document.querySelectorAll('input[name="source"]:checked');
    sourceCheckboxes.forEach(checkbox => {
        selectedSources.push(checkbox.value);
    });
    
    return {
        interested_keywords: userPreferences.interested_keywords,
        blocked_keywords: userPreferences.blocked_keywords,
        preferred_sources: selectedSources,
        min_priority_score: parseFloat(document.getElementById('min-priority').value),
        max_articles_per_page: parseInt(document.getElementById('max-articles').value),
        notification_enabled: document.getElementById('notifications-enabled').checked,
        notification_priority_threshold: parseFloat(document.getElementById('notification-threshold').value)
    };
}

function resetToDefaults() {
    if (confirm('모든 설정을 기본값으로 초기화하시겠습니까?')) {
        // 기본값 설정
        userPreferences = {
            interested_keywords: ['AI', '인공지능', '머신러닝', 'deep learning', '5nm', '3nm', '2nm'],
            blocked_keywords: [],
            preferred_sources: ['EE Times', '전자신문', 'Semiconductor Engineering', 'AnandTech', "Tom's Hardware"],
            min_priority_score: 0.0,
            max_articles_per_page: 20,
            notification_enabled: true,
            notification_priority_threshold: 7.0
        };
        
        populateForm();
        showToast('설정이 기본값으로 초기화되었습니다.', 'info');
    }
}

function goBack() {
    window.location.href = '/';
}

// 유틸리티 함수들
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
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