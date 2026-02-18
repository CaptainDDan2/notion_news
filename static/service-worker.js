/**
 * Service Worker - 오프라인 지원 및 캐싱
 * 모바일 앱 성능 향상
 */

const CACHE_NAME = 'semiconductor-news-v1';
const RUNTIME_CACHE = 'runtime-cache';

// 캐시할 필수 파일들
const ESSENTIAL_ASSETS = [
  '/',
  '/static/style.css',
  '/static/script.js',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png'
];

// Service Worker 설치
self.addEventListener('install', (event) => {
  console.log('Service Worker 설치 중...');
  
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('필수 자산 캐싱 중...');
      return cache.addAll(ESSENTIAL_ASSETS);
    })
  );
});

// Service Worker 활성화
self.addEventListener('activate', (event) => {
  console.log('Service Worker 활성화됨');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE) {
            console.log('이전 캐시 삭제:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// 캐시 우선 전략 (오프라인 지원)
self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // GET 요청만 처리
  if (request.method !== 'GET') {
    return;
  }
  
  // API 요청 (네트워크 우선)
  if (request.url.includes('/api/')) {
    event.respondWith(networkFirst(request));
  }
  // 정적 자산 (캐시 우선)
  else if (request.url.includes('/static/')) {
    event.respondWith(cacheFirst(request));
  }
  // HTML 페이지 (네트워크 우선)
  else {
    event.respondWith(networkFirst(request));
  }
});

// 네트워크 우선 전략
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    
    // 성공 응답만 캐시
    if (response.status === 200) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // 네트워크 실패 시 캐시에서 로드
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    
    // 캐시도 없으면 오프라인 페이지
    return caches.match('/offline.html');
  }
}

// 캐시 우선 전략
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  
  try {
    const response = await fetch(request);
    
    if (response.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('요청 실패:', error);
    throw error;
  }
}

// 백그라운드 동기
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-news') {
    event.waitUntil(syncNews());
  }
});

async function syncNews() {
  try {
    const response = await fetch('/api/articles?limit=10');
    const data = await response.json();
    
    // IndexedDB에 저장
    const db = await openDatabase();
    await saveToIndexedDB(db, 'articles', data);
  } catch (error) {
    console.error('뉴스 동기화 실패:', error);
  }
}

// IndexedDB 헬퍼
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('semiconductor-news', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('articles')) {
        db.createObjectStore('articles', { keyPath: 'id' });
      }
    };
  });
}

function saveToIndexedDB(db, storeName, data) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    
    data.forEach(item => {
      store.put(item);
    });
    
    transaction.onerror = () => reject(transaction.error);
    transaction.oncomplete = () => resolve();
  });
}

// 정기적인 재로드
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
