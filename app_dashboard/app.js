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
        fetchRecentKnowledge()
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
            <td><span class="badge badge-type">${typeLabel}</span></td>
            <td>${entry.metadata.summary || entry.document.substring(0, 50) + '...'}</td>
            <td>${category}</td>
            <td><span class="badge badge-verified">🕷️ ${status}</span></td>
            <td>
                <button class="btn-danger" onclick="deleteEntry('${entry.id}')" data-testid="delete-${entry.id}">
                    Delete
                </button>
            </td>
        `;
        tbody.appendChild(row);
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

    // Expose deleteEntry to global scope for onclick handlers
    window.deleteEntry = deleteEntry;
}
