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
        delete fileInput.dataset.redactedContent; // Clear previous redaction
        const redactBtn = document.getElementById('gap-auto-redact-btn');
        if (redactBtn) redactBtn.disabled = true;
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
                    ${((entry.image || entry.metadata.screenshot) && (entry.image || entry.metadata.screenshot).length > 100) ? `
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

    // Handle Current Image
    const currentImage = document.getElementById('edit-current-image');
    // Hide the old preview element if it exists
    const oldPreview = document.getElementById('edit-image-preview');
    if (oldPreview) oldPreview.style.display = 'none';

    if (currentImage) {
        const imgSrc = entry.image || entry.metadata.screenshot;
        if (imgSrc && imgSrc.length > 100) {
            let src = imgSrc;
            if (!src.startsWith('data:image')) {
                src = 'data:image/png;base64,' + src;
            }
            currentImage.src = src;
            currentImage.style.display = 'block';

            // Show Auto-Redact button for existing image
            const redactBtn = document.getElementById('edit-auto-redact-btn');
            if (redactBtn) {
                redactBtn.style.display = 'inline-block';
                redactBtn.disabled = false;
                redactBtn.textContent = '✨ Auto-Redact (HIPAA)';
            }
        } else {
            currentImage.style.display = 'none';
            currentImage.src = '';
            const redactBtn = document.getElementById('edit-auto-redact-btn');
            if (redactBtn) redactBtn.style.display = 'none';
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

    // Prioritize redacted content (whether from new upload or existing image)
    if (fileInput.dataset.redactedContent) {
        screenshot = fileInput.dataset.redactedContent.split(',')[1]; // Remove data:image/...;base64, prefix
    } else if (fileInput.files.length > 0) {
        // Fallback if no redacted content but new file selected
        screenshot = await readFileAsBase64(fileInput.files[0]);
        screenshot = screenshot.split(',')[1];
    }

    const btn = document.getElementById('save-edit-btn');
    const originalText = btn.textContent;
    // btn.textContent = 'Saving...'; // Moved down to set dynamic text
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

        // Check if we should trigger re-analysis
        // We trigger it if content or screenshot changed
        // Since we don't have the original content easily accessible here without fetching, 
        // we'll assume if the user is saving, they might want re-analysis if they touched the content field.
        // A safer bet is to ask the user, but for now we'll do it automatically if content is present.

        let url = `${API_BASE_URL}/knowledge/${id}`;
        let statusText = 'Saving...';

        // Simple heuristic: if content length > 0, we request re-analysis to keep tags in sync
        // Or we could check if it's different from what we loaded.
        // Let's just always re-analyze on edit for now as per requirements "Trigger a fresh AI analysis upon edit"
        url += '?reanalyze=true';
        statusText = 'Re-analyzing & Saving...';

        btn.textContent = statusText;

        const response = await fetch(url, {
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
    // Remove old listener by cloning (simplest way to clear anonymous listeners)
    const newFileInput = fileInput.cloneNode(true);
    fileInput.parentNode.replaceChild(newFileInput, fileInput);

    newFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImageUpload(e.target.files[0], (base64) => {
                const preview = document.getElementById('edit-preview');
                const container = document.getElementById('edit-preview-container');
                const redactBtn = document.getElementById('edit-auto-redact-btn');

                if (preview && container) {
                    preview.src = base64;
                    preview.style.opacity = '1';
                    container.style.display = 'block';

                    // Store on the element for saveEdit to access
                    newFileInput.dataset.redactedContent = base64;

                    if (redactBtn) {
                        redactBtn.style.display = 'inline-block';
                        redactBtn.disabled = false;
                        redactBtn.textContent = '✨ Auto-Redact (HIPAA)';
                    }
                }
            });
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
    if (fileInput) {
        if (fileInput.dataset.redactedContent) {
            screenshot = fileInput.dataset.redactedContent.split(',')[1];
        } else if (fileInput.files.length > 0) {
            try {
                // Convert to Base64 using FileReader as requested
                const base64Data = await readFileAsBase64(fileInput.files[0]);
                // Remove prefix if present (readFileAsBase64 returns full data URL)
                screenshot = base64Data.split(',')[1];
            } catch (err) {
                console.error('Failed to read screenshot:', err);
            }
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

        // Victory Highlight Logic
        setTimeout(() => {
            const tbody = document.getElementById('knowledge-table-body');
            if (tbody && tbody.firstElementChild) {
                const newRow = tbody.firstElementChild;
                newRow.classList.add('highlight-pulse');
                newRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

                // Remove class after animation to clean up
                setTimeout(() => {
                    newRow.classList.remove('highlight-pulse');
                }, 2000);
            }
        }, 100); // Small delay to ensure render completes

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

    setupRedactionListeners();
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

    setupRedactionListeners();
    setupAutoRedactButtons();
}

function setupAutoRedactButtons() {
    // Gap Section
    const gapFileInput = document.getElementById('gap-screenshot-input');
    const gapRedactBtn = document.getElementById('gap-auto-redact-btn');
    const gapKeepBtn = document.getElementById('gap-keep-btn');
    const gapRevertBtn = document.getElementById('gap-revert-btn');

    if (gapFileInput && gapRedactBtn) {
        gapFileInput.addEventListener('change', () => {
            gapRedactBtn.disabled = gapFileInput.files.length === 0;
            // Reset state on new file
            if (gapFileInput.files.length > 0) {
                gapRedactBtn.style.display = 'inline-block';
                gapRedactBtn.textContent = '✨ Auto-Redact (HIPAA)';
                gapRedactBtn.disabled = false;
                if (gapKeepBtn) gapKeepBtn.style.display = 'none';
                if (gapRevertBtn) gapRevertBtn.style.display = 'none';
                delete gapFileInput.dataset.redactedContent;
            }
        });

        gapRedactBtn.addEventListener('click', () => {
            if (gapFileInput.files.length > 0) {
                const originalText = gapRedactBtn.textContent;
                gapRedactBtn.textContent = 'Redacting...';
                gapRedactBtn.disabled = true;

                handleImageUpload(gapFileInput.files[0], (base64) => {
                    // Store redacted content
                    gapFileInput.dataset.redactedContent = base64;

                    // Update UI
                    gapRedactBtn.style.display = 'none';
                    gapRedactBtn.textContent = originalText;
                    gapRedactBtn.disabled = false;

                    if (gapKeepBtn) gapKeepBtn.style.display = 'inline-block';
                    if (gapRevertBtn) gapRevertBtn.style.display = 'inline-block';
                });
            }
        });

        if (gapKeepBtn) {
            gapKeepBtn.addEventListener('click', () => {
                gapKeepBtn.textContent = '🛡️ Protected';
                gapKeepBtn.disabled = true;
                if (gapRevertBtn) gapRevertBtn.style.display = 'none';
            });
        }

        if (gapRevertBtn) {
            gapRevertBtn.addEventListener('click', () => {
                delete gapFileInput.dataset.redactedContent;

                gapRedactBtn.style.display = 'inline-block';
                if (gapKeepBtn) {
                    gapKeepBtn.style.display = 'none';
                    gapKeepBtn.textContent = '🛡️ Keep Protected';
                    gapKeepBtn.disabled = false;
                }
                gapRevertBtn.style.display = 'none';
            });
        }
    }

    // Edit Modal
    // Edit Modal
    const editFileInput = document.getElementById('edit-screenshot');
    const editRedactBtn = document.getElementById('edit-auto-redact-btn');
    const editKeepBtn = document.getElementById('edit-keep-btn');
    const editRevertBtn = document.getElementById('edit-revert-btn');

    if (editFileInput && editRedactBtn) {
        // Note: editFileInput has a 'change' listener already that handles preview.

        editFileInput.addEventListener('change', () => {
            if (editFileInput.files.length > 0) {
                editRedactBtn.style.display = 'inline-block';
                if (editKeepBtn) editKeepBtn.style.display = 'none';
                if (editRevertBtn) editRevertBtn.style.display = 'none';
                delete editFileInput.dataset.redactedContent; // Clear previous redaction
            }
        });

        editRedactBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const originalText = editRedactBtn.textContent;
            editRedactBtn.textContent = 'Redacting...';
            editRedactBtn.disabled = true;

            let fileToRedact = null;

            if (editFileInput.files.length > 0) {
                fileToRedact = editFileInput.files[0];
            } else {
                // Check for existing image
                const currentImage = document.getElementById('edit-current-image');
                if (currentImage && currentImage.src && currentImage.style.display !== 'none') {
                    try {
                        const response = await fetch(currentImage.src);
                        const blob = await response.blob();
                        fileToRedact = new File([blob], "existing_image.png", { type: blob.type });
                    } catch (err) {
                        console.error("Failed to convert existing image to file:", err);
                        alert("Could not process existing image.");
                        editRedactBtn.textContent = originalText;
                        editRedactBtn.disabled = false;
                        return;
                    }
                }
            }

            if (fileToRedact) {
                handleImageUpload(fileToRedact, (base64) => {
                    // Update preview
                    const preview = document.getElementById('edit-preview');
                    const container = document.getElementById('edit-preview-container');
                    const currentImage = document.getElementById('edit-current-image');

                    if (preview && container) {
                        preview.src = base64;
                        container.style.display = 'block';
                        // Hide current image to show the redacted preview instead
                        if (currentImage) currentImage.style.display = 'none';
                    }

                    // Store for save
                    editFileInput.dataset.redactedContent = base64;

                    // Update Buttons
                    editRedactBtn.style.display = 'none';
                    editRedactBtn.textContent = originalText;
                    editRedactBtn.disabled = false;

                    if (editKeepBtn) editKeepBtn.style.display = 'inline-block';
                    if (editRevertBtn) editRevertBtn.style.display = 'inline-block';
                });
            } else {
                editRedactBtn.textContent = originalText;
                editRedactBtn.disabled = false;
            }
        });

        if (editKeepBtn) {
            editKeepBtn.addEventListener('click', () => {
                // Visual confirmation
                // Maybe disable Revert? Or just show a toast?
                // For now, let's just keep it simple: it stays in this state.
                // The dataset.redactedContent is already set.
                // We could hide the buttons to "lock" it, but user might want to revert later?
                // Mockup implies these buttons stay visible to allow choice.
                // But "Keep" implies an action.
                // Let's just disable Revert to show it's locked?
                // Or maybe hide both and show "Protected"?
                // Let's stick to the request: "Keep" commits it.
                // Since it's already in dataset, we just visually confirm.
                editKeepBtn.textContent = '🛡️ Protected';
                editKeepBtn.disabled = true;
                if (editRevertBtn) editRevertBtn.style.display = 'none';
            });
        }

        if (editRevertBtn) {
            editRevertBtn.addEventListener('click', () => {
                // Revert to original state
                delete editFileInput.dataset.redactedContent;

                const previewContainer = document.getElementById('edit-preview-container');
                const currentImage = document.getElementById('edit-current-image');

                if (previewContainer) previewContainer.style.display = 'none';

                if (editFileInput.files.length > 0) {
                    // Restore file preview
                    readFileAsBase64(editFileInput.files[0]).then(base64 => {
                        const preview = document.getElementById('edit-preview');
                        if (preview) preview.src = base64;
                        if (previewContainer) previewContainer.style.display = 'block';
                    });
                } else {
                    // Existing image case
                    if (currentImage) currentImage.style.display = 'block';
                }

                // Reset Buttons
                editRedactBtn.style.display = 'inline-block';
                if (editKeepBtn) {
                    editKeepBtn.style.display = 'none';
                    editKeepBtn.textContent = '🛡️ Keep Protected'; // Reset text
                    editKeepBtn.disabled = false;
                }
                editRevertBtn.style.display = 'none';
            });
        }
    }
}

// --- Redaction Logic ---
let redactionCanvas = null;
let redactionCtx = null;
let currentRedactionImage = null; // Image object
let currentRedactionScale = 1;
let isDrawing = false;
let startX, startY;
let redactionHistory = []; // Array of canvas states (base64)
let redactionCallback = null; // Function to call on save

// New state for version control
let originalRedactionImageSrc = null;
let protectedRedactionImageSrc = null;
let isProtectedMode = true;

function setupRedactionListeners() {
    const modal = document.getElementById('redaction-modal');
    const closeBtn = document.getElementById('close-redaction-modal-btn');
    const cancelBtn = document.getElementById('cancel-redaction-btn');
    const saveBtn = document.getElementById('save-redaction-btn');
    const undoBtn = document.getElementById('tool-undo');
    const resetBtn = document.getElementById('tool-reset');
    const canvas = document.getElementById('redaction-canvas');

    // New Buttons
    const btnKeep = document.getElementById('btn-keep-redacted');
    const btnRevert = document.getElementById('btn-revert-original');

    if (closeBtn) closeBtn.onclick = closeRedactionModal;
    if (cancelBtn) cancelBtn.onclick = closeRedactionModal;
    if (saveBtn) saveBtn.onclick = saveRedaction;

    if (undoBtn) undoBtn.onclick = () => {
        if (redactionHistory.length > 1) {
            redactionHistory.pop(); // Remove current state
            const previousState = redactionHistory[redactionHistory.length - 1];
            loadImageToCanvas(previousState);
        }
    };

    if (resetBtn) resetBtn.onclick = () => {
        // Reset to the base image of the current mode
        const baseSrc = isProtectedMode ? protectedRedactionImageSrc : originalRedactionImageSrc;
        redactionHistory = [baseSrc];
        loadImageToCanvas(baseSrc);
    };

    if (btnKeep) btnKeep.onclick = showProtectedVersion;
    if (btnRevert) btnRevert.onclick = showOriginalVersion;

    if (canvas) {
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);
    }
}

async function handleImageUpload(file, callback) {
    if (!file) return;

    // Show loading state (maybe a toast or global spinner)
    const statusEl = document.querySelector('[data-testid="connection-status"]');
    const originalStatus = statusEl.textContent;
    statusEl.textContent = 'Redacting...';

    try {
        // 1. Send to Backend for AI Redaction
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/redact`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errorData.detail || 'Redaction failed');
        }

        const data = await response.json();

        // 2. Open Modal with Redacted Image
        openRedactionModal(data.redacted_image, data.original_image, (finalBase64) => {
            callback(finalBase64);
        });

    } catch (error) {
        console.error('Redaction flow error:', error);
        alert(`Auto-redaction failed: ${error.message}`);
    } finally {
        statusEl.textContent = originalStatus;

        // Reset buttons if they were stuck in "Redacting..." state
        // We need to find which button triggered this. 
        // Since we don't pass the button element, we'll reset both potential buttons.
        const gapRedactBtn = document.getElementById('gap-auto-redact-btn');
        if (gapRedactBtn && gapRedactBtn.textContent === 'Redacting...') {
            gapRedactBtn.textContent = '✨ Auto-Redact (HIPAA)';
            gapRedactBtn.disabled = false;
        }

        const editRedactBtn = document.getElementById('edit-auto-redact-btn');
        if (editRedactBtn && editRedactBtn.textContent === 'Redacting...') {
            editRedactBtn.textContent = '✨ Auto-Redact (HIPAA)';
            editRedactBtn.disabled = false;
        }
    }
}

function openRedactionModal(redactedImageSrc, originalImageSrc, callback) {
    const modal = document.getElementById('redaction-modal');
    if (!modal) return;

    redactionCallback = callback;

    // Store versions
    protectedRedactionImageSrc = redactedImageSrc;
    originalRedactionImageSrc = originalImageSrc;

    // Initialize Canvas
    redactionCanvas = document.getElementById('redaction-canvas');
    redactionCtx = redactionCanvas.getContext('2d');

    // Default to Protected Mode
    showProtectedVersion();

    modal.showModal();
}

function showProtectedVersion() {
    isProtectedMode = true;
    redactionHistory = [protectedRedactionImageSrc];
    loadImageToCanvas(protectedRedactionImageSrc);
    updateRedactionUI();
}

function showOriginalVersion() {
    isProtectedMode = false;
    redactionHistory = [originalRedactionImageSrc];
    loadImageToCanvas(originalRedactionImageSrc);
    updateRedactionUI();
}

function updateRedactionUI() {
    const btnKeep = document.getElementById('btn-keep-redacted');
    const btnRevert = document.getElementById('btn-revert-original');
    const badge = document.getElementById('redaction-status-badge');
    const helpText = document.getElementById('redaction-help-text');

    if (isProtectedMode) {
        btnKeep.classList.add('active');
        btnKeep.style.borderColor = '#00C853';
        btnRevert.classList.remove('active');
        btnRevert.style.borderColor = 'var(--border-color)';

        badge.textContent = '🛡️ Protected';
        badge.style.backgroundColor = '#00C853';

        helpText.textContent = 'Confirming the protected version ensures PII is removed before saving.';
    } else {
        btnRevert.classList.add('active');
        btnRevert.style.borderColor = '#F85149';
        btnKeep.classList.remove('active');
        btnKeep.style.borderColor = 'var(--border-color)';

        badge.textContent = '⚠️ Unsafe';
        badge.style.backgroundColor = '#F85149';

        helpText.textContent = 'Warning: You are about to save the original image with potential PII exposed.';
    }
}

function closeRedactionModal() {
    const modal = document.getElementById('redaction-modal');
    if (modal) modal.close();
    redactionCallback = null;
}

function saveRedaction() {
    if (!redactionCanvas || !redactionCallback) return;
    const finalBase64 = redactionCanvas.toDataURL('image/png');
    redactionCallback(finalBase64);
    closeRedactionModal();
}

function loadImageToCanvas(src, pushToHistory = false) {
    const img = new Image();
    img.onload = () => {
        currentRedactionImage = img;
        redactionCanvas.width = img.width;
        redactionCanvas.height = img.height;
        redactionCtx.drawImage(img, 0, 0);

        if (pushToHistory) {
            redactionHistory.push(src);
        }
    };
    img.src = src;
}

// Canvas Drawing Logic
function startDrawing(e) {
    isDrawing = true;
    const rect = redactionCanvas.getBoundingClientRect();
    const scaleX = redactionCanvas.width / rect.width;
    const scaleY = redactionCanvas.height / rect.height;

    startX = (e.clientX - rect.left) * scaleX;
    startY = (e.clientY - rect.top) * scaleY;
}

function draw(e) {
    if (!isDrawing) return;

    const rect = redactionCanvas.getBoundingClientRect();
    const scaleX = redactionCanvas.width / rect.width;
    const scaleY = redactionCanvas.height / rect.height;

    const currentX = (e.clientX - rect.left) * scaleX;
    const currentY = (e.clientY - rect.top) * scaleY;

    // Redraw image to clear previous rectangle preview
    redactionCtx.drawImage(currentRedactionImage, 0, 0);

    // Draw rectangle
    redactionCtx.fillStyle = 'black';
    redactionCtx.fillRect(
        startX,
        startY,
        currentX - startX,
        currentY - startY
    );
}

function stopDrawing(e) {
    if (!isDrawing) return;
    isDrawing = false;

    // Save state
    const newBase64 = redactionCanvas.toDataURL('image/png');
    redactionHistory.push(newBase64);

    // Update current image reference for next draw
    const img = new Image();
    img.src = newBase64;
    img.onload = () => {
        currentRedactionImage = img;
    };
}

// Helper for direct redaction (if needed by legacy code, though we should use handleImageUpload)
// Helper for direct redaction
async function redactImage(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/redact`, {
            method: 'POST',
            headers: {
                'X-API-Key': API_KEY
            },
            body: formData
        });

        if (!response.ok) throw new Error('Redaction failed');
        const data = await response.json();
        // The backend returns the full data URI
        return data.redacted_image;
    } catch (error) {
        console.error('Direct redaction failed:', error);
        throw error;
    }
}

// Ensure global scope exposure
window.deleteEntry = deleteEntry;
window.openEditModal = openEditModal;
window.restoreEntry = restoreEntry;
window.switchTab = switchTab;
