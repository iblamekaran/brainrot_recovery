// PWA Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('Service Worker Registered'))
      .catch(err => console.log('Service Worker failed:', err));
  });
}

// PWA Install prompt handling
let deferredPrompt = null;
const btnInstall = document.getElementById('btnInstall');

// Theme Switcher Logic
const btnThemeToggle = document.getElementById('btnThemeToggle');
const themeIcon = document.getElementById('themeIcon');

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('brainrot_theme', theme);
  if (themeIcon) {
    themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    btnThemeToggle.title = theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode';
  }
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) {
    metaTheme.setAttribute('content', theme === 'light' ? '#FFFFFF' : '#7C3AED');
  }
}

// Sync initial icon state
const activeTheme = localStorage.getItem('brainrot_theme') ||
  (document.documentElement.getAttribute('data-theme') || 'dark');
applyTheme(activeTheme);

if (btnThemeToggle) {
  btnThemeToggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = current === 'dark' ? 'light' : 'dark';
    applyTheme(nextTheme);
  });
}

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  if (btnInstall) btnInstall.style.display = 'flex';
});

if (btnInstall) {
  btnInstall.addEventListener('click', async () => {
    if (!deferredPrompt) {
      alert("To install:\n• On Android: Tap Chrome's menu (⋮) -> 'Install app' or 'Add to Home screen'\n• On iPhone: Tap Safari's Share button -> 'Add to Home Screen'");
      return;
    }
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      btnInstall.style.display = 'none';
    }
    deferredPrompt = null;
  });
}

// Application State
let topicsData = [];
let activeTopic = null;
let currentTechFilter = 'All';
let currentStatusFilter = 'All';
let currentSearch = '';

// DOM Elements
const overallPctEl = document.getElementById('overallPct');
const overallProgressFillEl = document.getElementById('overallProgressFill');
const valTotalEl = document.getElementById('valTotal');
const valCoveredEl = document.getElementById('valCovered');
const subCoveredEl = document.getElementById('subCovered');
const valInProgEl = document.getElementById('valInProg');
const valRevEl = document.getElementById('valRev');
const subRevEl = document.getElementById('subRev');

const searchInputEl = document.getElementById('searchInput');
const topicsListEl = document.getElementById('topicsList');
const topicCountEl = document.getElementById('topicCount');

// Modal Elements
const modalOverlayEl = document.getElementById('modalOverlay');
const modalSheetTitleEl = document.getElementById('modalSheetTitle');
const modalTechEl = document.getElementById('modalTech');
const modalSectionEl = document.getElementById('modalSection');
const modalConceptsEl = document.getElementById('modalConcepts');
const modalAppEl = document.getElementById('modalApp');
const modalDateInputEl = document.getElementById('modalDateInput');
const modalNotesInputEl = document.getElementById('modalNotesInput');
const btnTodayEl = document.getElementById('btnToday');
const btnSaveModalEl = document.getElementById('btnSaveModal');
const btnCloseModalEl = document.getElementById('btnCloseModal');
const btnExportExcelEl = document.getElementById('btnExportExcel');
const toastEl = document.getElementById('toast');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadSummary();
  loadTopics();
  setupFilterHandlers();
});

// Load summary from API
async function loadSummary() {
  try {
    const res = await fetch('/api/summary');
    const data = await res.json();
    renderSummary(data);
    localStorage.setItem('vyavastha_summary_cache', JSON.stringify(data));
  } catch (err) {
    // Offline fallback
    const cached = localStorage.getItem('vyavastha_summary_cache');
    if (cached) renderSummary(JSON.parse(cached));
  }
}

function renderSummary(data) {
  const pct = data.pct_covered || 0;
  overallPctEl.textContent = `${pct.toFixed(1)}%`;
  overallProgressFillEl.style.width = `${pct}%`;

  valTotalEl.textContent = data.total;
  valCoveredEl.textContent = data.covered;
  subCoveredEl.textContent = `${pct.toFixed(1)}% completed`;

  valInProgEl.textContent = data.in_progress;
  valRevEl.textContent = data.revision;
  subRevEl.textContent = `${data.not_started} not started`;
}

// Load topics list
async function loadTopics() {
  try {
    const res = await fetch('/api/topics');
    topicsData = await res.json();
    localStorage.setItem('vyavastha_topics_cache', JSON.stringify(topicsData));
    applyFiltersAndRender();
  } catch (err) {
    // Offline fallback
    const cached = localStorage.getItem('vyavastha_topics_cache');
    if (cached) {
      topicsData = JSON.parse(cached);
      applyFiltersAndRender();
    }
  }
}

function setupFilterHandlers() {
  // Search
  searchInputEl.addEventListener('input', (e) => {
    currentSearch = e.target.value.toLowerCase().trim();
    applyFiltersAndRender();
  });

  // Status Filter Chips
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentStatusFilter = chip.dataset.status;
      applyFiltersAndRender();
    });
  });

  // Technology Tabs
  document.querySelectorAll('.tech-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tech-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTechFilter = tab.dataset.tech;
      applyFiltersAndRender();
    });
  });

  // Status button selection inside Modal
  document.querySelectorAll('.status-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.status-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');

      // Auto-set date if Covered
      if (btn.dataset.status === 'Covered' && !modalDateInputEl.value.trim()) {
        setTodayDate();
      }
    });
  });

  // Date today button
  btnTodayEl.addEventListener('click', setTodayDate);

  // Close modal
  btnCloseModalEl.addEventListener('click', closeModal);
  modalOverlayEl.addEventListener('click', (e) => {
    if (e.target === modalOverlayEl) closeModal();
  });

  // Save Modal
  btnSaveModalEl.addEventListener('click', saveActiveTopic);

  // Export Excel
  btnExportExcelEl.addEventListener('click', exportToExcel);
}

function setTodayDate() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  modalDateInputEl.value = `${yyyy}-${mm}-${dd}`;
}

function applyFiltersAndRender() {
  const filtered = topicsData.filter(topic => {
    // Tech filter
    if (currentTechFilter !== 'All' && topic.technology !== currentTechFilter) {
      return false;
    }
    // Status filter
    if (currentStatusFilter !== 'All' && topic.status !== currentStatusFilter) {
      return false;
    }
    // Search query
    if (currentSearch) {
      const matchTopic = topic.topic.toLowerCase().includes(currentSearch);
      const matchSection = (topic.section || '').toLowerCase().includes(currentSearch);
      const matchSub = (topic.subtopics || '').toLowerCase().includes(currentSearch);
      const matchNotes = (topic.practice_notes || '').toLowerCase().includes(currentSearch);
      if (!matchTopic && !matchSection && !matchSub && !matchNotes) {
        return false;
      }
    }
    return true;
  });

  topicCountEl.textContent = `Showing ${filtered.length} of ${topicsData.length} topics`;
  renderTopicsList(filtered);
}

function renderTopicsList(topics) {
  if (topics.length === 0) {
    topicsListEl.innerHTML = `
      <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
        <p style="font-size: 16px; margin-bottom: 6px;">No topics found</p>
        <p style="font-size: 12px;">Try adjusting your search or filters</p>
      </div>
    `;
    return;
  }

  topicsListEl.innerHTML = topics.map(t => {
    const statusClass = `status-${t.status.replace(/\s+/g, '-')}`;
    const badgeClass = t.technology === 'JDBC' ? 'badge-jdbc' : 'badge-core';
    const notesPart = t.practice_notes ? `<span class="topic-notes-preview">“${t.practice_notes}”</span>` : '<span></span>';
    const datePart = t.date_covered ? `📅 ${t.date_covered}` : 'Tap to edit';

    return `
      <div class="topic-card" onclick="openTopicModal(${t.id})">
        <div class="card-top-row">
          <div class="topic-num-tech">
            <span>#${t.id}</span>
            <span class="badge-tag ${badgeClass}">${t.technology}</span>
          </div>
          <div class="status-badge ${statusClass}">
            ${t.status}
          </div>
        </div>
        <div class="topic-title">${escapeHtml(t.topic)}</div>
        <div class="topic-section">${escapeHtml(t.section)}</div>
        <div class="topic-footer">
          ${notesPart}
          <span>${datePart}</span>
        </div>
      </div>
    `;
  }).join('');
}

// Open Topic Details Bottom Sheet
function openTopicModal(topicId) {
  const topic = topicsData.find(t => t.id === topicId);
  if (!topic) return;

  activeTopic = topic;
  modalSheetTitleEl.textContent = `#${topic.id} · ${topic.topic}`;
  modalTechEl.textContent = `${topic.technology} — Priority: ${topic.priority}`;
  modalSectionEl.textContent = topic.section;
  modalConceptsEl.textContent = topic.subtopics || 'No subtopics specified.';
  modalAppEl.textContent = topic.vyavastha_app || 'Core programming foundation.';

  modalDateInputEl.value = topic.date_covered || '';
  modalNotesInputEl.value = topic.practice_notes || '';

  // Set selected status button
  document.querySelectorAll('.status-btn').forEach(btn => {
    btn.classList.toggle('selected', btn.dataset.status === topic.status);
  });

  modalOverlayEl.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modalOverlayEl.classList.remove('active');
  document.body.style.overflow = '';
  activeTopic = null;
}

// Save topic updates
async function saveActiveTopic() {
  if (!activeTopic) return;

  const selectedBtn = document.querySelector('.status-btn.selected');
  const newStatus = selectedBtn ? selectedBtn.dataset.status : activeTopic.status;
  const newDate = modalDateInputEl.value.trim() || null;
  const newNotes = modalNotesInputEl.value.trim() || null;

  btnSaveModalEl.textContent = 'Saving...';
  btnSaveModalEl.disabled = true;

  try {
    const res = await fetch(`/api/topics/${activeTopic.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: newStatus,
        date_covered: newDate,
        practice_notes: newNotes
      })
    });

    const result = await res.json();
    if (result.success) {
      // Update local state
      activeTopic.status = newStatus;
      activeTopic.date_covered = newDate;
      activeTopic.practice_notes = newNotes;

      closeModal();
      showToast('✓ Progress saved successfully!');
      loadSummary();
      applyFiltersAndRender();
    } else {
      alert('Error saving topic: ' + result.error);
    }
  } catch (err) {
    alert('Failed to connect to server. Check connection.');
  } finally {
    btnSaveModalEl.textContent = 'Save Progress';
    btnSaveModalEl.disabled = false;
  }
}

// Export progress to Excel
async function exportToExcel() {
  btnExportExcelEl.textContent = 'Exporting...';
  try {
    const res = await fetch('/api/export-excel', { method: 'POST' });
    const result = await res.json();
    if (result.success) {
      showToast('✓ Synced with Excel workbook!');
    } else {
      alert('Export error: ' + result.error);
    }
  } catch (err) {
    alert('Failed to connect to server.');
  } finally {
    btnExportExcelEl.textContent = '📊 Sync Excel';
  }
}

// Helper: Toast notification
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add('show');
  setTimeout(() => {
    toastEl.classList.remove('show');
  }, 3200);
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, function(m) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    }[m];
  });
}
