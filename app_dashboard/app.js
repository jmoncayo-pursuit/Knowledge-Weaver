/**
 * Knowledge-Weaver Dashboard Logic
 * AI-Native, Robot-Accessible, and Fast.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';
const API_KEY = 'dev-secret-key-12345'; // In production, this should be handled securely

// --- Robot Logging Utility ---
async function logBarrier(selector, error) {
    try {
        console.error(`[RobotBarrier] ${error} at ${selector}`);
        await fetch(`${API_BASE_URL}/log/barrier`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({
                url: window.location.href,
                selector: selector,
                error: error,
                agent: 'Dashboard JS',
                timestamp: new Date().toISOString()
            })
        });
    } catch (e) {
        console.error('Failed to log barrier:', e);
    }
}

// --- API Helper ---
async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            }
        };
        if (body) options.body = JSON.stringify(body);

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Call Failed (${endpoint}):`, error);
        document.querySelector('[data-testid="connection-status"]').textContent = 'Connection Error';
        document.querySelector('[data-testid="connection-status"]').style.color = '#F85149';
        return null;
    }
}

// --- State ---
let selectedGap = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    initDashboard();
});

async function initDashboard() {
    updateStatus('Connected');
    await Promise.all([
        fetchMetrics(),
        fetchKnowledgeGaps(),
        fetchRecentKnowledge(),
        loadLearningHistory(),
        fetchRecentKnowledge(),
        loadLearningHistory(),
        fetchLearningStats(),
        fetchCognitiveHealth()
    ]);

    setupEventListeners();
}

function updateStatus(status) {
    const el = document.querySelector('[data-testid="connection-status"]');
    if (el) {
        el.textContent = status;
        el.style.color = '#00C853';
    }
}

// --- Metrics ---
async function fetchMetrics() {
    const data = await apiCall('/metrics/dashboard');
    if (!data) return;

    updateMetric('metric-total-knowledge', data.total_knowledge);
    updateMetric('metric-verified-ratio', `${data.verified_ratio}%`);
    updateMetric('metric-query-volume', data.query_volume_7d);
    updateMetric('metric-knowledge-gaps', data.knowledge_gaps_7d);
}

function updateMetric(testId, value) {
    const el = document.querySelector(`[data-testid="${testId}"] .value`);
    if (el) el.textContent = value;
    else logBarrier(`[data-testid="${testId}"]`, 'Metric element not found');
}

// --- Knowledge Gaps ---
async function fetchKnowledgeGaps() {
    const data = await apiCall('/metrics/dashboard'); // Gaps are in dashboard metrics
    if (!data || !data.recent_gaps) return;

    const listEl = document.getElementById('gap-list');
    if (!listEl) {
        logBarrier('#gap-list', 'Gap list container not found');
        return;
    }

    listEl.innerHTML = '';

    if (data.recent_gaps.length === 0) {
        listEl.innerHTML = '<div style="padding:1rem; color:#8B949E;">No active gaps found.</div>';
        return;
    }

    data.recent_gaps.forEach(gap => {
        const item = document.createElement('div');
        item.className = 'gap-item';
        item.setAttribute('data-testid', `gap-item-${gap.query.replace(/\s+/g, '-').toLowerCase()}`);
        item.innerHTML = `
            <span class="gap-query">${gap.query}</span>
            <span class="gap-count">${gap.count} attempts</span>
        `;
        item.onclick = () => selectGap(gap.query, item);
        listEl.appendChild(item);
    });
}

function selectGap(query, element) {
    selectedGap = query;

    // Update UI
    document.querySelectorAll('.gap-item').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');

    document.getElementById('selected-gap-display').textContent = `Solving: "${query}"`;
    document.getElementById('selected-gap-query').value = query;

    // Enable form
    const input = document.getElementById('answer-content');
    const fileInput = document.getElementById('gap-screenshot-input');
    const btn = document.querySelector('[data-testid="submit-answer-btn"]');

    input.disabled = false;
    if (fileInput) {
        fileInput.disabled = false;
        fileInput.value = ''; // Clear previous selection
    }
    btn.disabled = false;
    input.focus();
}

// --- Recent Knowledge ---
async function fetchRecentKnowledge() {
    const entries = await apiCall('/knowledge/recent?limit=10');
    if (!entries) return;

    const tbody = document.getElementById('knowledge-table-body');
    if (!tbody) {
        logBarrier('#knowledge-table-body', 'Table body not found');
        return;
    }

    tbody.innerHTML = '';

    entries.forEach(entry => {
        const row = document.createElement('tr');

        // Polish: Format type labels
        let typeLabel = entry.metadata.type || 'unknown';
        if (typeLabel === 'manual_ingestion') typeLabel = 'Verified Capture';
        if (typeLabel === 'chat_log') typeLabel = 'Auto-Capture';

        const category = entry.metadata.category || 'Uncategorized';
        const status = entry.metadata.verification_status === 'verified_human' ? 'Verified' : 'Draft';

        row.innerHTML = `
            <td data-label="Type"><span class="badge badge-type">${typeLabel}</span></td>
            <td data-label="Content">${entry.metadata.summary || entry.document.substring(0, 50) + '...'}</td>
            <td data-label="Category">${category}</td>
            <td data-label="Status"><span class="badge badge-verified">🕷️ ${status}</span></td>
            <td data-label="Actions">
                <div class="action-container">
                    ${(entry.metadata.screenshot && entry.metadata.screenshot.length > 100) ? `
                    <button class="btn-secondary view-image-btn" 
                        data-id="${entry.id}"
                        style="font-size: 12px; padding: 4px 8px;">
                        📷 View
                    </button>` : ''}
                    <button class="btn-primary edit-btn" 
                        data-id="${entry.id}" 
                        data-category="${escapeHtml(category)}" 
                        data-tags="${escapeHtml(entry.metadata.tags || '')}" 
                        data-summary="${escapeHtml(entry.metadata.summary || '')}"
                        data-testid="edit-${entry.id}" 
                        style="font-size: 12px; padding: 4px 8px;">
                        Edit
                    </button>
                    <button class="btn-danger delete-btn" 
                        data-id="${entry.id}" 
                        data-testid="delete-${entry.id}" 
                        style="font-size: 12px; padding: 4px 8px;">
                        Delete
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

}

// --- Learning History ---
async function loadLearningHistory() {
    const tbody = document.getElementById('learning-table-body');
    if (!tbody) return;

    const history = await apiCall('/metrics/learning?limit=5');

    if (!history || history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 2rem; color: var(--text-secondary);">No learning activity yet. Teach the AI by correcting its suggestions!</td></tr>';
        return;
    }

    tbody.innerHTML = history.map(event => {
        const date = new Date(event.timestamp).toLocaleString();

        // Helper to format content
        const formatContent = (data) => {
            if (!data) return '<span style="color: var(--text-secondary)">-</span>';
            const cat = data.category ? `<div><span class="badge badge-type" style="font-size: 10px;">Cat</span> ${data.category}</div>` : '';
            const tags = data.tags && data.tags.length ? `<div><span class="badge badge-type" style="font-size: 10px;">Tags</span> ${data.tags.join(', ')}</div>` : '';
            return `<div style="display:flex; flex-direction:column; gap:4px;">${cat}${tags}</div>`;
        };

        const original = formatContent(event.ai_prediction);
        const correction = formatContent(event.human_correction);

        return `
            <tr>
                <td>${original}</td>
                <td>${correction}</td>
                <td style="font-size: 12px; color: var(--text-secondary);">${date}</td>
            </tr>
        `;
    }).join('');
}

// --- Learning Stats (Chart.js) ---
async function fetchLearningStats() {
    const data = await apiCall('/metrics/learning_stats');
    if (!data || !data.top_learned_tags) return;

    const ctx = document.getElementById('learning-chart');
    if (!ctx) return;

    // Destroy existing chart if any
    if (window.learningChart) {
        window.learningChart.destroy();
    }

    const labels = data.top_learned_tags.map(item => item.tag);
    const counts = data.top_learned_tags.map(item => item.count);

    window.learningChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Corrections by Tag',
                data: counts,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// --- Cognitive Health (Chart.js) ---
async function fetchCognitiveHealth() {
    const data = await apiCall('/metrics/cognitive_health');
    if (!data) return;

    const ctx = document.getElementById('cognitive-health-chart');
    if (!ctx) return;

    // Destroy existing chart if any
    if (window.cognitiveHealthChart) {
        window.cognitiveHealthChart.destroy();
    }

    const labels = data.map(item => item.date);
    const errorRates = data.map(item => item.error_rate);

    window.cognitiveHealthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'AI Error Rate (%)',
                data: errorRates,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.4 // Smooth curves
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Error Rate (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `Error Rate: ${context.parsed.y}%`;
                        }
                    }
                }
            }
        }
    });
}

// --- Edit Modal Logic ---
// Removed top-level const to ensure we get the element when needed
// const editModal = document.getElementById('edit-modal'); 
// const editForm = document.getElementById('edit-form');

async function openEditModal(id) {
    const editModal = document.getElementById('edit-modal');
    if (!editModal) return;

    // Fetch fresh data to ensure we have the full content and correct types
    const entries = await apiCall('/knowledge/recent?limit=50');
    const entry = entries.find(e => e.id === id);

    if (!entry) {
        alert('Entry not found');
        return;
    }

    document.getElementById('edit-id').value = id;
    document.getElementById('edit-category').value = entry.metadata.category || '';

    // Handle Tags (Array or String)
    let tags = entry.metadata.tags || '';
    if (Array.isArray(tags)) {
        tags = tags.join(', ');
    }
    document.getElementById('edit-tags').value = tags;

    // Handle Summary/Content
    document.getElementById('edit-summary').value = entry.metadata.summary || '';
    document.getElementById('edit-content-input').value = entry.document || entry.content || '';

    // Reset screenshot input
    document.getElementById('edit-screenshot').value = '';
    document.getElementById('edit-preview-container').style.display = 'none';
    document.getElementById('edit-preview').src = '';

    // Handle Current Image (using new ID as requested)
    const imagePreview = document.getElementById('edit-image-preview');
    // Also handle old ID just in case, but hide it to avoid duplicates if both exist
    const oldImage = document.getElementById('edit-current-image');
    if (oldImage) oldImage.style.display = 'none';

    if (imagePreview) {
        if (entry.metadata.screenshot) {
            let src = entry.metadata.screenshot;
            if (!src.startsWith('data:image')) {
                src = 'data:image/png;base64,' + src;
            }
            imagePreview.src = src;
            imagePreview.style.display = 'block';
        } else {
            imagePreview.style.display = 'none';
            imagePreview.src = '';
        }
    }

    editModal.showModal();
}

function closeEditModal() {
    const editModal = document.getElementById('edit-modal');
    if (editModal) editModal.close();
}

async function openImageModal(id) {
    const modal = document.getElementById('image-modal');
    const img = document.getElementById('full-size-image');

    if (!modal || !img) return;

    const entries = await apiCall('/knowledge/recent?limit=50');
    const entry = entries.find(e => e.id === id);

    if (entry && entry.metadata.screenshot) {
        let src = entry.metadata.screenshot;
        // Fix: Ensure data URI prefix
        if (!src.startsWith('data:image')) {
            src = 'data:image/png;base64,' + src;
        }
        img.src = src;
        img.style.display = 'block';
        img.style.maxWidth = '100%';
        modal.showModal();
    } else {
        alert('Image not found.');
    }
}

function closeImageModal() {
    const modal = document.getElementById('image-modal');
    if (modal) modal.close();
}

async function saveEdit(e) {
    e.preventDefault();

    const id = document.getElementById('edit-id').value;
    const category = document.getElementById('edit-category').value;
    const tags = document.getElementById('edit-tags').value.split(',').map(t => t.trim()).filter(t => t);
    const summary = document.getElementById('edit-summary').value;
    const content = document.getElementById('edit-content-input').value;

    // Handle Screenshot
    let screenshot = null;
    const fileInput = document.getElementById('edit-screenshot');
    if (fileInput.files.length > 0) {
        screenshot = await readFileAsBase64(fileInput.files[0]);
    }

    const btn = document.getElementById('save-edit-btn');
    const originalText = btn.textContent;
    btn.textContent = 'Saving...';
    btn.disabled = true;

    try {
        const payload = {
            category,
            tags,
            summary,
            content, // Added content field
            screenshot
        };

        // Remove screenshot if null to avoid clearing it unintentionally? 
        // The backend probably handles partial updates or we send what we have.
        // The original code sent 'screenshot' even if null (which was initialized to null).
        // If the user didn't select a new file, screenshot is null.
        // If we send null, does it clear the image?
        // The original code:
        /*
            body: JSON.stringify({
                category,
                tags,
                summary,
                screenshot
            })
        */
        // I will keep it consistent.

        const response = await fetch(`${API_BASE_URL}/knowledge/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            closeEditModal();
            fetchRecentKnowledge(); // Refresh table
            loadLearningHistory(); // Refresh history if relevant
        } else {
            alert('Failed to save changes');
        }
    } catch (error) {
        console.error('Save failed:', error);
        alert('Error saving changes');
    }

    btn.textContent = originalText;
    btn.disabled = false;
}

// Helper for HTML escaping in onclick attributes
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Helper to read file as Base64
function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

// File Input Listener for Preview
const fileInput = document.getElementById('edit-screenshot');
if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
        if (e.target.files.length > 0) {
            const base64 = await readFileAsBase64(e.target.files[0]);
            const preview = document.getElementById('edit-preview');
            const container = document.getElementById('edit-preview-container');
            if (preview && container) {
                preview.src = base64;
                container.style.display = 'block';
            }
        }
    });
}

// --- Actions ---
async function submitGapAnswer(e) {
    e.preventDefault();

    if (!selectedGap) return;

    const content = document.getElementById('answer-content').value;
    if (!content) return;

    const btn = document.querySelector('[data-testid="submit-answer-btn"]');
    const originalText = btn.textContent;
    btn.textContent = 'Submitting...';
    btn.disabled = true;

    // Handle Screenshot
    let screenshot = null;
    const fileInput = document.getElementById('gap-screenshot-input');
    if (fileInput && fileInput.files.length > 0) {
        try {
            screenshot = await readFileAsBase64(fileInput.files[0]);
        } catch (err) {
            console.error('Failed to read screenshot:', err);
        }
    }

    const success = await apiCall('/ingest', 'POST', {
        text: content,
        url: 'dashboard_manual_entry',
        category: 'Gap Resolution',
        tags: ['#GapResolution'],
        summary: selectedGap, // Use the gap query as the summary for resolution tracking
        screenshot: screenshot
    });

    if (success) {
        // Clear form
        document.getElementById('answer-content').value = '';
        selectedGap = null;
        document.getElementById('selected-gap-display').textContent = 'Select a gap to answer...';
        document.getElementById('answer-content').disabled = true;
        const fileInput = document.getElementById('gap-screenshot-input');
        if (fileInput) {
            fileInput.value = '';
            fileInput.disabled = true;
        }

        // Refresh data
        await Promise.all([fetchMetrics(), fetchKnowledgeGaps(), fetchRecentKnowledge()]);
    } else {
        alert('Failed to submit answer.');
    }

    btn.textContent = originalText;
    // Keep disabled until new selection
}

async function deleteEntry(id) {
    // Barrier Removed: window.confirm blocks robots. 
    // In a real app, we would use a non-blocking toast with "Undo".

    const success = await apiCall(`/knowledge/${id}`, 'DELETE');
    if (success) {
        fetchRecentKnowledge();
        fetchMetrics();
    } else {
        alert('Failed to delete entry.');
    }
}

async function restoreEntry(id) {
    const success = await apiCall(`/knowledge/${id}/restore`, 'POST');
    if (success) {
        fetchDeletedKnowledge();
        fetchMetrics();
    } else {
        alert('Failed to restore entry.');
    }
}

// --- Tab Switching ---
function switchTab(tab) {
    // Update Buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    // Use ID based selection if possible, otherwise fallback to onclick attribute finding (legacy support)
    const btn = document.getElementById(tab === 'active' ? 'tab-active' : 'tab-recycle');
    if (btn) btn.classList.add('active');

    // Update Views
    const activeView = document.getElementById('active-knowledge-view');
    const recycleView = document.getElementById('recycle-bin-view');
    const refreshBtn = document.getElementById('refresh-knowledge-btn');

    if (tab === 'active') {
        activeView.classList.remove('hidden');
        recycleView.classList.add('hidden');
        fetchRecentKnowledge();
        refreshBtn.onclick = fetchRecentKnowledge;
    } else {
        activeView.classList.add('hidden');
        recycleView.classList.remove('hidden');
        fetchDeletedKnowledge();
        refreshBtn.onclick = fetchDeletedKnowledge;
    }
}

// --- Recycle Bin Data ---
async function fetchDeletedKnowledge() {
    const entries = await apiCall('/knowledge/recent?limit=20&deleted_only=true');
    if (!entries) return;

    const tbody = document.getElementById('recycle-table-body');
    const emptyState = document.getElementById('recycle-empty-state');

    if (!tbody) return;

    tbody.innerHTML = '';

    if (entries.length === 0) {
        emptyState.style.display = 'block';
        return;
    } else {
        emptyState.style.display = 'none';
    }

    entries.forEach(entry => {
        const row = document.createElement('tr');

        let typeLabel = entry.metadata.type || 'unknown';
        const category = entry.metadata.category || 'Uncategorized';
        const deletedAt = new Date().toLocaleDateString(); // Metadata doesn't store deleted_at yet, using current for demo

        row.innerHTML = `
            <td data-label="Type"><span class="badge badge-type">${typeLabel}</span></td>
            <td data-label="Content">${entry.metadata.summary || entry.document.substring(0, 50) + '...'}</td>
            <td data-label="Category">${category}</td>
            <td data-label="Deleted At">${deletedAt}</td>
            <td data-label="Actions">
                <div class="action-container">
                    <button class="btn-primary restore-btn" 
                        data-id="${entry.id}" 
                        data-testid="restore-${entry.id}" 
                        style="font-size: 12px; padding: 4px 8px;">
                        Restore ♻️
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// --- Event Listeners ---
function setupEventListeners() {
    const form = document.getElementById('gap-answer-form');
    if (form) {
        form.addEventListener('submit', submitGapAnswer);
    } else {
        logBarrier('#gap-answer-form', 'Gap answer form not found');
    }

    const refreshBtn = document.getElementById('refresh-knowledge-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchRecentKnowledge);
    }

    // Modal Listeners
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const editForm = document.getElementById('edit-form');
    const editModal = document.getElementById('edit-modal');

    if (closeModalBtn) closeModalBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent any default action
        closeEditModal();
    });
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', (e) => {
        e.preventDefault();
        closeEditModal();
    });
    if (editForm) editForm.addEventListener('submit', saveEdit);

    const closeImageModalBtn = document.getElementById('close-image-modal-btn');
    if (closeImageModalBtn) {
        closeImageModalBtn.addEventListener('click', closeImageModal);
    }

    const imageModal = document.getElementById('image-modal');
    if (imageModal) {
        imageModal.addEventListener('click', (e) => {
            if (e.target === imageModal) closeImageModal();
        });
    }

    // Tab Listeners
    const tabActive = document.getElementById('tab-active');
    const tabRecycle = document.getElementById('tab-recycle');

    if (tabActive) {
        tabActive.addEventListener('click', () => switchTab('active'));
    }
    if (tabRecycle) {
        tabRecycle.addEventListener('click', () => switchTab('recycle'));
    }

    // Event Delegation for Active Knowledge Table
    const activeView = document.getElementById('active-knowledge-view');
    if (activeView) {
        activeView.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-btn');
            const deleteBtn = e.target.closest('.delete-btn');
            const viewImgBtn = e.target.closest('.view-image-btn');

            if (editBtn) {
                const { id } = editBtn.dataset;
                openEditModal(id);
            } else if (deleteBtn) {
                const { id } = deleteBtn.dataset;
                deleteEntry(id);
            } else if (viewImgBtn) {
                const { id } = viewImgBtn.dataset;
                openImageModal(id);
            }
        });
    }

    // Event Delegation for Recycle Bin Table
    const recycleView = document.getElementById('recycle-bin-view');
    if (recycleView) {
        recycleView.addEventListener('click', (e) => {
            const restoreBtn = e.target.closest('.restore-btn');
            if (restoreBtn) {
                const { id } = restoreBtn.dataset;
                restoreEntry(id);
            }
        });
    }

    // Modal Backdrop Click
    if (editModal) {
        editModal.addEventListener('click', (e) => {
            if (e.target === editModal) {
                closeEditModal();
            }
        });
    }
}

// Ensure global scope exposure
window.deleteEntry = deleteEntry;
window.openEditModal = openEditModal;
window.restoreEntry = restoreEntry;
window.switchTab = switchTab;
