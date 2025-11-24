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
        fetchLearningStats()
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
    const btn = document.querySelector('[data-testid="submit-answer-btn"]');

    input.disabled = false;
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
                <button class="btn-primary" onclick="openEditModal('${entry.id}', '${escapeHtml(category)}', '${escapeHtml(entry.metadata.tags || '')}', '${escapeHtml(entry.metadata.summary || '')}')" data-testid="edit-${entry.id}" style="margin-right: 5px; font-size: 12px; padding: 4px 8px;">
                    Edit
                </button>
                <button class="btn-danger" onclick="deleteEntry('${entry.id}')" data-testid="delete-${entry.id}" style="font-size: 12px; padding: 4px 8px;">
                    Delete
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

}

// --- Learning History ---
async function loadLearningHistory() {
    const feed = document.getElementById('learning-feed');
    if (!feed) return;

    const history = await apiCall('/metrics/learning?limit=5');

    if (!history || history.length === 0) {
        feed.innerHTML = '<div class="empty-state">No learning activity yet. Teach the AI by correcting its suggestions!</div>';
        return;
    }

    feed.innerHTML = history.map(event => {
        const date = new Date(event.timestamp).toLocaleString();

        // Calculate diffs
        const oldTags = event.ai_prediction.tags || [];
        const newTags = event.human_correction.tags || [];
        const oldCat = event.ai_prediction.category || 'None';
        const newCat = event.human_correction.category || 'None';

        let diffHtml = '';

        // Category Diff
        if (oldCat !== newCat) {
            diffHtml += `
                <div class="learning-diff">
                    <span class="diff-label">Category:</span>
                    <span class="diff-old">${oldCat}</span>
                    <span class="diff-arrow">→</span>
                    <span class="diff-new">${newCat}</span>
                </div>
            `;
        }

        // Tags Diff (Simplified for demo)
        const addedTags = newTags.filter(t => !oldTags.includes(t));
        if (addedTags.length > 0) {
            diffHtml += `
                <div class="learning-diff">
                    <span class="diff-label">Learned Tags:</span>
                    <span class="diff-new">+ ${addedTags.join(', ')}</span>
                </div>
            `;
        }

        return `
            <div class="learning-card">
                <div class="learning-header">
                    <span>🤖 AI Training Event</span>
                    <span>${date}</span>
                </div>
                ${diffHtml}
                <div class="learning-summary">"${event.summary}"</div>
            </div>
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

// --- Edit Modal Logic ---
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-form');

function openEditModal(id, category, tags, summary) {
    if (!editModal) return;

    document.getElementById('edit-id').value = id;
    document.getElementById('edit-category').value = category;
    document.getElementById('edit-tags').value = tags;
    document.getElementById('edit-summary').value = summary;

    // Reset screenshot input
    document.getElementById('edit-screenshot').value = '';
    document.getElementById('edit-preview-container').style.display = 'none';
    document.getElementById('edit-preview').src = '';

    editModal.showModal();
}

function closeEditModal() {
    if (editModal) editModal.close();
}

async function saveEdit(e) {
    e.preventDefault();

    const id = document.getElementById('edit-id').value;
    const category = document.getElementById('edit-category').value;
    const tags = document.getElementById('edit-tags').value.split(',').map(t => t.trim()).filter(t => t);
    const summary = document.getElementById('edit-summary').value;

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
        const response = await fetch(`${API_BASE_URL}/knowledge/${id}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({
                category,
                tags,
                summary,
                screenshot
            })
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

    const success = await apiCall('/ingest', 'POST', {
        text: content,
        url: 'dashboard_manual_entry',
        category: 'Gap Resolution',
        tags: ['#GapResolution'],
        summary: selectedGap // Use the gap query as the summary for resolution tracking
    });

    if (success) {
        // Clear form
        document.getElementById('answer-content').value = '';
        selectedGap = null;
        document.getElementById('selected-gap-display').textContent = 'Select a gap to answer...';
        document.getElementById('answer-content').disabled = true;

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

    if (closeModalBtn) closeModalBtn.addEventListener('click', closeEditModal);
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditModal);
    if (editForm) editForm.addEventListener('submit', saveEdit);
}

// Ensure global scope exposure
window.deleteEntry = deleteEntry;
window.openEditModal = openEditModal;
window.restoreEntry = restoreEntry;
window.switchTab = switchTab;
