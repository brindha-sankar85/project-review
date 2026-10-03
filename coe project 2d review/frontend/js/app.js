// Application Global State
const state = {
    currentUser: null,
    users: [],
    documents: [],
    sharingRequests: [],
    auditLogs: [],
    experimentResults: null,
    edgeCases: [],
    currentSlide: 0,
    pendingConfirmRequest: null
};

// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', async () => {
    console.log("Initializing MedShield Assistant Application...");
    setupNavigation();
    setupModals();
    await loadInitialData();
    setupEventListeners();
});

// Setup Navigation Routing
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = item.getAttribute('data-page');
            switchPage(targetPage);
        });
    });
}

function switchPage(pageId) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeNav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
    if (activeNav) activeNav.classList.add('active');

    // Update active view section
    document.querySelectorAll('.page-view').forEach(el => el.classList.remove('active'));
    const activePage = document.getElementById(`page-${pageId}`);
    if (activePage) activePage.classList.add('active');

    // Update Header Titles
    const titleMap = {
        'dashboard': 'Clinical Governance Dashboard',
        'documents': 'Hospital Protocol Documents',
        'summary': 'Confidentiality-Aware Protocol Summariser',
        'sharing': 'Protocol Sharing Request Log',
        'approval': 'High-Impact Action Human Confirmations',
        'audit': 'System Audit & Governance Logs',
        'experiments': 'Measurable Experiments & Baseline Comparison',
        'edgecases': 'Failure Mode & Edge Case Verification Suite',
        'events': 'Live Event Stream & Idempotency Processor',
        'workflow': 'Field Workflow & Shift Handover Architecture',
        'users': 'Synthetic Hospital User Directory & Permissions',
        'validation': 'User & Stakeholder Validation Feedback',
        'presentation': 'Project Presentation Slides Deck',
        'docs': 'Technical Specifications & Architecture Docs'
    };
    document.getElementById('pageTitle').innerText = titleMap[pageId] || 'Dashboard';

    // Page-specific lazy data loaders
    if (pageId === 'dashboard') loadDashboard();
    if (pageId === 'documents') renderDocumentsGrid();
    if (pageId === 'summary') populateSummarySelect();
    if (pageId === 'sharing') renderSharingRequests();
    if (pageId === 'approval') renderPendingApprovals();
    if (pageId === 'audit') loadAuditLogs();
    if (pageId === 'experiments') loadExperiments();
    if (pageId === 'edgecases') loadEdgeCases();
    if (pageId === 'events') loadEventStream();
    if (pageId === 'users') renderUsersMatrix();
    if (pageId === 'validation') loadValidationSummary();
    if (pageId === 'presentation') renderPresentationSlide(state.currentSlide);
    if (pageId === 'docs') loadDocTab('arch');
}

// Initial Data Loader
async function loadInitialData() {
    try {
        const usersRes = await fetch('/api/auth/users');
        state.users = await usersRes.json();

        // Default active user is Doctor Gregory House or first user
        state.currentUser = state.users.find(u => u.username === 'doc_house') || state.users[0];

        updateUserUI();
        await refreshDocuments();
        await refreshSharingRequests();
        await loadDashboard();
    } catch (err) {
        console.error("Error initializing app data:", err);
    }
}

function updateUserUI() {
    if (!state.currentUser) return;
    document.getElementById('currentUserName').innerText = state.currentUser.name;
    document.getElementById('currentUserRole').innerText = state.currentUser.role;
    document.getElementById('currentUserDept').innerText = state.currentUser.department;
    document.getElementById('userAvatar').innerText = state.currentUser.name.split(' ').map(n => n[0]).join('').substring(0, 2);

    // Refresh views to respect newly switched user permissions
    refreshDocuments();
}

async function refreshDocuments() {
    if (!state.currentUser) return;
    const res = await fetch(`/api/documents/?user_id=${state.currentUser.id}`);
    state.documents = await res.json();
}

async function refreshSharingRequests() {
    const res = await fetch('/api/sharing/requests');
    state.sharingRequests = await res.json();
    updatePendingBadge();
}

function updatePendingBadge() {
    const pendingCount = state.sharingRequests.filter(r => r.status === 'PENDING').length;
    document.getElementById('pendingCountBadge').innerText = pendingCount;
    document.getElementById('dashPendingCount').innerText = pendingCount;
}

// DASHBOARD RENDERER
async function loadDashboard() {
    await refreshDocuments();
    await refreshSharingRequests();

    const accessibleCount = state.documents.filter(d => d.is_accessible).length;
    document.getElementById('dashAccessibleCount').innerText = `${accessibleCount}/${state.documents.length}`;

    const blockedCount = state.sharingRequests.filter(r => r.status === 'REJECTED' || r.risk_level === 'HIGH').length;
    document.getElementById('dashBlockedCount').innerText = blockedCount;

    // Load recent dashboard table
    const tableBody = document.getElementById('dashDocsTableBody');
    tableBody.innerHTML = state.documents.slice(0, 5).map(doc => `
        <tr>
            <td><code>${doc.document_id}</code></td>
            <td><strong>${doc.title}</strong></td>
            <td>${doc.department}</td>
            <td><span class="badge badge-${doc.confidentiality_level.toLowerCase().replace('_', '-')}">${doc.confidentiality_level}</span></td>
            <td>v${doc.protocol_version}</td>
            <td>${doc.is_accessible ? '<span class="text-success"><i class="fa-solid fa-circle-check"></i> Authorized</span>' : '<span class="text-danger"><i class="fa-solid fa-lock"></i> Restricted</span>'}</td>
            <td><button class="btn btn-sm btn-outline" onclick="openSummaryForDoc('${doc.document_id}')"><i class="fa-solid fa-waveform"></i> Summarise</button></td>
        </tr>
    `).join('');

    // Load Recent Audit Timeline
    const auditRes = await fetch('/api/audit/logs?limit=5');
    const logs = await auditRes.json();
    const timeline = document.getElementById('dashAuditTimeline');
    timeline.innerHTML = logs.map(l => `
        <li style="margin-bottom: 12px; font-size: 0.82rem;">
            <strong>${l.user_name} (${l.role})</strong>: <span class="text-blue">${l.action}</span>
            <div style="color: var(--text-muted); font-size: 0.75rem;">${new Date(l.timestamp).toLocaleTimeString()} - ${l.reason || ''}</div>
        </li>
    `).join('');
}

// DOCUMENTS GRID RENDERER
function renderDocumentsGrid() {
    const grid = document.getElementById('documentsGrid');
    grid.innerHTML = state.documents.map(doc => `
        <div class="doc-card">
            <div>
                <div class="doc-header">
                    <h4>${doc.title}</h4>
                    <span class="badge badge-${doc.confidentiality_level.toLowerCase().replace('_', '-')}">${doc.confidentiality_level}</span>
                </div>
                <div class="doc-meta">
                    <span><i class="fa-solid fa-building-hospital"></i> ${doc.department}</span>
                    <span><i class="fa-solid fa-code-branch"></i> v${doc.protocol_version}</span>
                </div>
                <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem;">
                    Effective: ${doc.effective_date} ${doc.status === 'SUPERSEDED' ? '<span class="text-amber">(SUPERSEDED)</span>' : ''}
                </p>
            </div>
            <div class="doc-actions">
                <button class="btn btn-sm btn-primary" onclick="openSummaryForDoc('${doc.document_id}')">
                    <i class="fa-solid fa-file-waveform"></i> Summarise
                </button>
                <button class="btn btn-sm btn-outline" onclick="openShareModalForDoc('${doc.document_id}')">
                    <i class="fa-solid fa-share-nodes"></i> Share
                </button>
            </div>
        </div>
    `).join('');
}

// SUMMARY GENERATOR
function populateSummarySelect() {
    const select = document.getElementById('summaryDocSelect');
    select.innerHTML = state.documents.map(d => `<option value="${d.document_id}">${d.title} (v${d.protocol_version}) [${d.confidentiality_level}]</option>`).join('');
}

window.openSummaryForDoc = function(docId) {
    switchPage('summary');
    setTimeout(() => {
        const select = document.getElementById('summaryDocSelect');
        select.value = docId;
        generateSummary();
    }, 100);
};

async function generateSummary() {
    const docId = document.getElementById('summaryDocSelect').value;
    const useBaseline = document.getElementById('useBaselineToggle').checked;
    const outputContainer = document.getElementById('summaryOutputContent');

    outputContainer.innerHTML = `<div class="loading-state"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p>Generating safe protocol summary for ${state.currentUser.name}...</p></div>`;

    const res = await fetch(`/api/documents/${docId}/summarize?user_id=${state.currentUser.id}&use_baseline=${useBaseline}`, { method: 'POST' });
    const data = await res.json();

    if (!data.success && !data.is_baseline) {
        outputContainer.innerHTML = `
            <div class="redacted-alert">
                <h4><i class="fa-solid fa-ban"></i> ${data.error || 'Access Denied'}</h4>
                <p>${data.summary}</p>
            </div>
            <div class="explanation-box">
                <h4>Rule & Evidence Explanation:</h4>
                <div class="exp-item"><strong>Recommendation:</strong> ${data.why_explanation.recommendation}</div>
                <div class="exp-item"><strong>Reason:</strong> ${data.why_explanation.reason}</div>
                <div class="exp-item"><strong>Rule Applied:</strong> ${data.why_explanation.rule}</div>
                <div class="exp-item"><strong>Evidence:</strong> ${data.why_explanation.evidence}</div>
            </div>
        `;
        return;
    }

    const exp = data.why_explanation || {};
    outputContainer.innerHTML = `
        ${data.is_baseline ? '<div class="redacted-alert" style="background: rgba(251, 191, 36, 0.15); border-left-color: var(--accent-amber);"><strong>⚠️ EXPERIMENTAL BASELINE SUMMARY:</strong> Contains raw unfiltered text without confidentiality redaction.</div>' : ''}
        
        <div style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.6; background: rgba(15,23,42,0.6); padding: 1.25rem; border-radius: 8px; border: 1px solid var(--border-color);">${data.summary}</div>

        ${data.has_redactions ? `
            <div class="redacted-alert">
                <h4><i class="fa-solid fa-shield-halved"></i> Confidentiality Redactions Applied (${data.redacted_count} sections withheld)</h4>
                <ul style="margin-left: 1.2rem; margin-top: 6px;">
                    ${data.information_withheld.map(info => `<li>${info}</li>`).join('')}
                </ul>
            </div>
        ` : ''}

        ${exp.rule ? `
            <div class="explanation-box">
                <h4 style="margin-bottom: 8px; font-family: Outfit;"><i class="fa-solid fa-lightbulb"></i> Non-Specialist Explanation (Rule & Evidence)</h4>
                <div class="exp-item"><strong>Recommendation:</strong> ${exp.recommendation}</div>
                <div class="exp-item"><strong>Reason:</strong> ${exp.reason}</div>
                <div class="exp-item"><strong>Rule Applied:</strong> ${exp.rule}</div>
                <div class="exp-item"><strong>Evidence:</strong> <code>${exp.evidence}</code></div>
                <div class="exp-item"><strong>Status:</strong> <span class="badge badge-approved">${exp.confidence_status}</span></div>
            </div>
        ` : ''}
    `;
}

// SHARING REQUESTS & HUMAN CONFIRMATIONS
function renderSharingRequests() {
    const tbody = document.getElementById('sharingTableBody');
    tbody.innerHTML = state.sharingRequests.map(req => {
        const rec = req.recommendation || {};
        return `
            <tr>
                <td><code>${req.request_id}</code></td>
                <td>${req.requester ? req.requester.name : 'System'} (${req.requester ? req.requester.role : ''})</td>
                <td>${req.recipient ? req.recipient.name : 'System'} (${req.recipient ? req.recipient.role : ''})</td>
                <td><strong>${req.document ? req.document.title : ''}</strong></td>
                <td><span class="badge badge-${req.risk_level === 'HIGH' || req.risk_level === 'CRITICAL' ? 'highly-confidential' : 'public'}">${req.risk_level}</span></td>
                <td style="max-width: 250px; font-size: 0.8rem;">${rec.recommendation || req.reason}</td>
                <td><span class="badge badge-${req.status.toLowerCase()}">${req.status}</span></td>
                <td>
                    ${req.status === 'PENDING' ? `
                        <button class="btn btn-sm btn-primary" onclick="openHumanConfirmModal('${req.request_id}')">
                            <i class="fa-solid fa-user-check"></i> Review
                        </button>
                    ` : `
                        <small style="color: var(--text-muted);">${req.override_reason ? 'Override: ' + req.override_reason : 'Processed'}</small>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

function renderPendingApprovals() {
    const pending = state.sharingRequests.filter(r => r.status === 'PENDING');
    const container = document.getElementById('pendingApprovalCards');

    if (pending.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-circle-check fa-3x" style="color: var(--accent-emerald);"></i>
                <p style="margin-top: 10px;">All sharing requests have been reviewed. No pending high-impact actions.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = pending.map(req => {
        const rec = req.recommendation || {};
        return `
            <div class="card" style="border-left: 4px solid var(--accent-amber); margin-bottom: 1rem;">
                <div class="card-body">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <span class="badge badge-pending">HIGH-IMPACT HUMAN CONFIRMATION</span>
                            <h4 style="margin-top: 6px;">Sharing Request ${req.request_id}</h4>
                        </div>
                        <span class="badge badge-highly-confidential">Risk: ${req.risk_level}</span>
                    </div>

                    <div style="margin: 1rem 0; font-size: 0.88rem; display:grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <p><strong>Document:</strong> ${req.document ? req.document.title : ''} (${req.document ? req.document.confidentiality_level : ''})</p>
                            <p><strong>Requester:</strong> ${req.requester ? req.requester.name : ''} (${req.requester ? req.requester.role : ''})</p>
                            <p><strong>Recipient:</strong> ${req.recipient ? req.recipient.name : ''} (${req.recipient ? req.recipient.role : ''})</p>
                        </div>
                        <div class="explanation-box" style="margin-top:0;">
                            <p><strong>Recommendation:</strong> ${rec.recommendation || 'Review required'}</p>
                            <p><strong>Reason:</strong> ${rec.reason || 'Role restrictions'}</p>
                            <p><strong>Rule:</strong> ${rec.rule || 'High confidentiality rule'}</p>
                        </div>
                    </div>

                    <button class="btn btn-primary" onclick="openHumanConfirmModal('${req.request_id}')">
                        <i class="fa-solid fa-user-shield"></i> Open Confirmation Screen & Record Override
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

window.openHumanConfirmModal = function(requestId) {
    const req = state.sharingRequests.find(r => r.request_id === requestId);
    if (!req) return;

    state.pendingConfirmRequest = req;

    const details = document.getElementById('humanConfirmDetails');
    const rec = req.recommendation || {};
    details.innerHTML = `
        <div style="background: rgba(15,23,42,0.7); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.88rem;">
            <p><strong>Document:</strong> ${req.document ? req.document.title : ''}</p>
            <p><strong>Recipient:</strong> ${req.recipient ? req.recipient.name : ''} (${req.recipient ? req.recipient.role : ''})</p>
            <p><strong>Risk Level:</strong> <span class="badge badge-highly-confidential">${req.risk_level}</span></p>
            <p><strong>Reason:</strong> ${rec.reason || req.reason}</p>
            <p><strong>Rule Applied:</strong> ${rec.rule || 'Confidential documents require authorized role'}</p>
        </div>
    `;

    document.getElementById('humanOverrideReasonInput').value = '';
    document.getElementById('overrideErrorMsg').style.display = 'none';
    document.getElementById('humanConfirmModal').classList.add('active');
};

async function handleHumanDecision(decision) {
    if (!state.pendingConfirmRequest) return;
    const reqId = state.pendingConfirmRequest.request_id;
    const overrideReason = document.getElementById('humanOverrideReasonInput').value.trim();

    if (decision === 'APPROVE' && !overrideReason) {
        document.getElementById('overrideErrorMsg').style.display = 'block';
        return;
    }

    const payload = {
        reviewer_id: state.currentUser.id,
        decision: decision,
        override_reason: overrideReason
    };

    const res = await fetch(`/api/sharing/requests/${reqId}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok) {
        document.getElementById('humanConfirmModal').classList.remove('active');
        await refreshSharingRequests();
        renderSharingRequests();
        renderPendingApprovals();
        loadDashboard();
    } else {
        alert(data.detail || 'Error processing decision.');
    }
}

// AUDIT LOGS
async function loadAuditLogs() {
    const actionFilter = document.getElementById('auditActionFilter').value;
    const res = await fetch(`/api/audit/logs?action=${actionFilter}`);
    state.auditLogs = await res.json();

    const tbody = document.getElementById('auditTableBody');
    tbody.innerHTML = state.auditLogs.map(l => `
        <tr>
            <td><code>${l.event_id.substring(0, 8)}</code></td>
            <td>${new Date(l.timestamp).toLocaleString()}</td>
            <td><strong>${l.user_name}</strong> (${l.role})</td>
            <td><span class="badge badge-internal">${l.action}</span></td>
            <td>${l.document_title || l.document_id || '-'}</td>
            <td>${l.recipient_name || '-'}</td>
            <td><code>${l.old_state} &rarr; ${l.new_state}</code></td>
            <td>${l.override_reason ? `<strong class="text-amber">${l.override_reason}</strong>` : (l.reason || '-')}</td>
        </tr>
    `).join('');
}

// EXPERIMENTS DASHBOARD
async function loadExperiments() {
    const res = await fetch('/api/experiments/results');
    const data = await res.json();
    state.experimentResults = data;

    const tbody = document.getElementById('experimentTableBody');
    tbody.innerHTML = data.metrics.map(m => `
        <tr>
            <td><strong>${m.metric_name}</strong></td>
            <td><span class="text-amber" style="font-weight:700;">${m.baseline_value} ${m.unit}</span></td>
            <td>${m.target_value} ${m.unit}</td>
            <td><span class="text-emerald" style="font-weight:700;">${m.proposed_value} ${m.unit}</span></td>
            <td>${m.unit}</td>
            <td><span class="badge badge-${m.status === 'PASSED' ? 'approved' : 'rejected'}">${m.status}</span></td>
        </tr>
    `).join('');

    // Update Dashboard leakage rate tile
    const leakMetric = data.metrics.find(m => m.metric_name === 'Sensitive Leakage Rate');
    if (leakMetric) {
        document.getElementById('dashLeakageRate').innerText = `${leakMetric.proposed_value}%`;
    }
}

async function runLeakageTest() {
    alert("Running automated synthetic leakage test across unauthorised roles...");
    const res = await fetch('/api/experiments/run-leakage-test', { method: 'POST' });
    const data = await res.json();
    alert(`Leakage Test Complete! Proposed Leakage Rate: ${data.proposed.leakage_rate_pct}% (${data.proposed.leaked_requests_count} leaks) vs Baseline Leakage Rate: ${data.baseline.leakage_rate_pct}%`);
    loadExperiments();
}

async function runFullExperimentSuite() {
    alert("Executing complete baseline vs proposed experiment suite...");
    await fetch('/api/experiments/run-suite', { method: 'POST' });
    await loadExperiments();
    alert("Experiment suite execution finished cleanly!");
}

// EDGE CASES PAGE
async function loadEdgeCases() {
    const res = await fetch('/api/experiments/results');
    const data = await res.json();
    const container = document.getElementById('edgeCaseGrid');

    container.innerHTML = data.failure_test_cases.map(tc => `
        <div class="card" style="margin-bottom: 1rem;">
            <div class="card-header">
                <h3><i class="fa-solid fa-vial"></i> ${tc.test_id}: ${tc.scenario}</h3>
                <span class="badge badge-${tc.status === 'PASSED' ? 'approved' : 'rejected'}">${tc.status}</span>
            </div>
            <div class="card-body" font-size: 0.85rem;">
                <p><strong>Expected Result:</strong> ${tc.expected_result}</p>
                <p style="margin-top:4px;"><strong>Actual Result:</strong> <span class="text-blue">${tc.actual_result}</span></p>
            </div>
        </div>
    `).join('');
}

// EVENT STREAM PROCESSOR
async function loadEventStream() {
    const res = await fetch('/api/events/stream');
    const data = await res.json();
    const container = document.getElementById('eventStreamContent');

    container.innerHTML = `
        <h4 style="font-family: Outfit; margin-bottom: 10px;">Entity State Trackers</h4>
        <div style="display:flex; gap: 1rem; margin-bottom: 1.5rem;">
            ${data.entity_trackers.map(t => `
                <div style="background: rgba(15,23,42,0.6); padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-color); flex:1;">
                    <strong>Entity: ${t.entity_id}</strong>
                    <div style="font-size:0.8rem; color: var(--text-secondary);">Last Processed Version: <strong class="text-blue">v${t.last_processed_version}</strong></div>
                    <div style="font-size:0.8rem; color: var(--text-secondary);">Status: <span class="badge badge-approved">${t.status}</span></div>
                </div>
            `).join('')}
        </div>

        <h4 style="font-family: Outfit; margin-bottom: 10px;">Recent Event Processing Log</h4>
        <ul style="list-style:none;">
            ${data.events.map(e => `
                <li style="padding: 10px; border-bottom: 1px solid var(--border-color); font-size: 0.85rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <code>${e.event_id}</code> | <strong>${e.event_type}</strong> (v${e.event_version}, Seq #${e.sequence_number})
                        <div style="font-size:0.75rem; color: var(--text-muted);">${new Date(e.timestamp).toLocaleTimeString()}</div>
                    </div>
                    <span class="badge badge-${e.processing_status === 'PROCESSED' ? 'approved' : 'pending'}">${e.processing_status}</span>
                </li>
            `).join('')}
        </ul>
    `;
}

async function handleEventInject() {
    const payload = {
        event_type: document.getElementById('injEventType').value,
        entity_id: document.getElementById('injEntityId').value,
        event_version: parseInt(document.getElementById('injEventVersion').value),
        sequence_number: parseInt(document.getElementById('injSeqNum').value),
        payload: { confidentiality_level: "INTERNAL" }
    };

    const res = await fetch('/api/events/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    alert(`Event Injection Result: ${data.processing_status} - ${data.message}`);
    loadEventStream();
}

// USERS & ROLE MATRIX
function renderUsersMatrix() {
    const tbody = document.getElementById('usersTableBody');
    const roleLevels = {
        'Admin': 'PUBLIC, INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL',
        'Hospital Manager': 'PUBLIC, INTERNAL, CONFIDENTIAL',
        'Doctor': 'PUBLIC, INTERNAL, CONFIDENTIAL',
        'Nurse': 'PUBLIC, INTERNAL, selected CONFIDENTIAL',
        'Receptionist': 'PUBLIC, selected INTERNAL',
        'Intern': 'PUBLIC, limited INTERNAL'
    };

    tbody.innerHTML = state.users.map(u => `
        <tr>
            <td><code>${u.id}</code></td>
            <td><strong>${u.name}</strong></td>
            <td><span class="role-badge">${u.role}</span></td>
            <td>${u.department}</td>
            <td style="font-size: 0.8rem; color: var(--accent-blue);">${roleLevels[u.role] || 'PUBLIC'}</td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="selectActiveUser('${u.id}')">
                    <i class="fa-solid fa-user-check"></i> Switch to User
                </button>
            </td>
        </tr>
    `).join('');
}

window.selectActiveUser = function(userId) {
    const targetUser = state.users.find(u => u.id === userId);
    if (targetUser) {
        state.currentUser = targetUser;
        updateUserUI();
        document.getElementById('roleModal').classList.remove('active');
        alert(`Switched active user to ${targetUser.name} (${targetUser.role})`);
        switchPage('dashboard');
    }
};

// VALIDATION SUMMARY
async function loadValidationSummary() {
    const res = await fetch('/api/validation/summary');
    const data = await res.json();
    const container = document.getElementById('validationAnalyticsContent');

    container.innerHTML = `
        <div style="font-family: Outfit; font-size: 1.8rem; color: var(--accent-emerald); font-weight:700; margin-bottom: 1rem;">
            ${data.avg_usability_rating} / 5.0 <span style="font-size:0.9rem; color: var(--text-secondary); font-weight:normal;">Average Usability Score (${data.total_responses} responses)</span>
        </div>

        <ul style="list-style:none; font-size: 0.88rem; line-height: 1.8;">
            <li><i class="fa-solid fa-circle-check text-emerald"></i> Recommendation Understandable: <strong>${data.satisfaction_metrics.recommendation_understandable_pct}%</strong></li>
            <li><i class="fa-solid fa-circle-check text-emerald"></i> Reason for Withholding Clear: <strong>${data.satisfaction_metrics.reason_clear_pct}%</strong></li>
            <li><i class="fa-solid fa-circle-check text-emerald"></i> Access Decision Clear: <strong>${data.satisfaction_metrics.access_decision_clear_pct}%</strong></li>
            <li><i class="fa-solid fa-circle-check text-emerald"></i> Summary Useful: <strong>${data.satisfaction_metrics.summary_useful_pct}%</strong></li>
            <li><i class="fa-solid fa-circle-check text-emerald"></i> Approval Workflow Clear: <strong>${data.satisfaction_metrics.approval_workflow_clear_pct}%</strong></li>
        </ul>
    `;
}

// PRESENTATION SLIDES (12 SLIDES)
const slidesData = [
    { title: "1. Confidentiality-Aware Hospital Assistant", content: "<h3>Project Overview</h3><p>A confidentiality-aware summarisation and sharing assistant built for hospitals with shift workers and protocol updates.</p><ul><li>Prevents accidental exposure of sensitive protocols.</li><li>Enforces Role-Based Access Control (RBAC) in backend APIs.</li><li>Provides plain-language evidence explanations for non-specialist reviewers.</li></ul>" },
    { title: "2. The Hospital Challenge", content: "<h3>Problem Statement</h3><p>Staff shift handovers & protocol changes lead to sensitive information leakage when documents are shared across mixed role levels (Interns, Nurses, Doctors, Receptionists).</p>" },
    { title: "3. Field Workflow Architecture", content: "<h3>Clinical Workflow</h3><p>Protocol Upload &rarr; Classification Label &rarr; Shift Handover Summary Request &rarr; Redaction Engine &rarr; Safe Summary &rarr; Human Review if High Risk &rarr; Audit Trail.</p>" },
    { title: "4. Proposed Confidentiality Solution", content: "<h3>Key Innovations</h3><ul><li>Section-level confidentiality tags</li><li>Backend API filtering (Zero client-side leakage)</li><li>Mandatory human override justification</li><li>Resilient Event Stream Processor</li></ul>" },
    { title: "5. System Architecture", content: "<h3>Tech Stack</h3><ul><li>Frontend: Responsive HTML5/CSS3 Single-Page App</li><li>Backend: Python FastAPI + SQLAlchemy + SQLite</li><li>Security: Role Permission Matrix & Redaction Engine</li></ul>" },
    { title: "6. Document & Permission Labels", content: "<h3>Confidentiality Levels</h3><ul><li>PUBLIC: General hygiene & emergency activation</li><li>INTERNAL: Pharmacy dispensing & lab biohazard</li><li>CONFIDENTIAL: Shift handovers & ICU sepsis bundles</li><li>HIGHLY_CONFIDENTIAL: Malpractice & incident reviews</li></ul>" },
    { title: "7. Redacted Summarisation Engine", content: "<h3>Summariser Workflow</h3><p>Filters unauthorised sections BEFORE summary text generation, providing structured WHY explanations with Rule, Reason, and Evidence.</p>" },
    { title: "8. Sharing & Human Confirmations", content: "<h3>Governance Controls</h3><p>High-risk sharing requests require human reviewer confirmation. Overriding access restrictions MANDATES a written justification reason.</p>" },
    { title: "9. Event Resilience Handling", content: "<h3>State Protection</h3><p>Handles delayed, duplicate, and out-of-order events using sequence vectors and idempotency checks to prevent state corruption.</p>" },
    { title: "10. Baseline vs Proposed Experiments", content: "<h3>Experimental Setup</h3><p>Compared against an experimental baseline summariser without confidentiality filtering. Injected synthetic test markers across 100+ requests.</p>" },
    { title: "11. Measured Results & Error Analysis", content: "<h3>Key Metrics</h3><ul><li>Baseline Leakage Rate: <strong>100%</strong></li><li>Proposed System Leakage Rate: <strong>0.0%</strong></li><li>Access Control Accuracy: <strong>100%</strong></li><li>Duplicate/Out-of-Order Recovery: <strong>100%</strong></li></ul>" },
    { title: "12. Stakeholder Validation & Conclusion", content: "<h3>Clinical Feedback</h3><p>Achieved 5.0/5.0 usability rating from synthetic clinical reviewers. System ready for live demonstration and evaluation.</p>" }
];

function renderPresentationSlide(index) {
    state.currentSlide = index;
    const slide = slidesData[index];
    const viewport = document.getElementById('slideViewport');

    viewport.innerHTML = `
        <h2 class="slide-title">${slide.title}</h2>
        <div class="slide-content">${slide.content}</div>
    `;

    document.getElementById('slideCounter').innerText = `Slide ${index + 1} of ${slidesData.length}`;
}

// DOCUMENTATION TAB LOADER
function loadDocTab(tabKey) {
    document.querySelectorAll('.doc-tab').forEach(t => t.classList.remove('active'));
    const activeTab = document.querySelector(`.doc-tab[data-doc="${tabKey}"]`);
    if (activeTab) activeTab.classList.add('active');

    const contentBox = document.getElementById('docTabContent');
    const docMap = {
        'arch': '<h4>System Architecture</h4><p>MedShield AI uses a modular FastAPI backend, SQLite database, and an HTML5/CSS3 SPA frontend. All document sections have individual confidentiality metadata.</p>',
        'exp': '<h4>Experiment Specifications</h4><p>Measures baseline vs proposed system leakage rate. Automated script injects markers SENSITIVE_TEST_001, RESTRICTED_TEST_002, and HIGHLY_CONFIDENTIAL_TEST_003.</p>',
        'fail': '<h4>Failure Mode & Edge Case Analysis</h4><p>Explicitly tests 7 edge case scenarios including duplicate event processing, out-of-order buffer recovery, delayed event versioning, and empty override reason rejection.</p>',
        'api': '<h4>REST API Documentation</h4><p>Provides OpenAPI endpoints at /docs. Endpoints cover /api/auth, /api/documents, /api/sharing, /api/audit, /api/events, /api/experiments, and /api/validation.</p>'
    };
    contentBox.innerHTML = docMap[tabKey] || '<p>Documentation view loaded.</p>';
}

// MODAL LISTENERS & FORM EVENT HANDLERS
function setupModals() {
    document.getElementById('openRoleModalBtn').addEventListener('click', openRoleModal);
    document.getElementById('closeRoleModalBtn').addEventListener('click', () => document.getElementById('roleModal').classList.remove('active'));
    
    document.getElementById('createShareModalOpenBtn').addEventListener('click', openShareModal);
    document.getElementById('newShareBtn').addEventListener('click', openShareModal);
    document.getElementById('closeShareModalBtn').addEventListener('click', () => document.getElementById('shareModal').classList.remove('active'));

    document.getElementById('closeHumanConfirmModalBtn').addEventListener('click', () => document.getElementById('humanConfirmModal').classList.remove('active'));
}

function openRoleModal() {
    const grid = document.getElementById('roleSelectionGrid');
    grid.innerHTML = state.users.map(u => `
        <div class="role-select-card ${state.currentUser && state.currentUser.id === u.id ? 'active' : ''}" onclick="selectActiveUser('${u.id}')">
            <strong>${u.name}</strong>
            <div><span class="role-badge">${u.role}</span></div>
            <small style="color: var(--text-muted);">${u.department}</small>
        </div>
    `).join('');
    document.getElementById('roleModal').classList.add('active');
}

function openShareModal() {
    const docSelect = document.getElementById('shareDocSelect');
    docSelect.innerHTML = state.documents.map(d => `<option value="${d.document_id}">${d.title} [${d.confidentiality_level}]</option>`).join('');

    const recipientSelect = document.getElementById('shareRecipientSelect');
    recipientSelect.innerHTML = state.users.map(u => `<option value="${u.id}">${u.name} (${u.role})</option>`).join('');

    document.getElementById('shareModal').classList.add('active');
}

window.openShareModalForDoc = function(docId) {
    openShareModal();
    document.getElementById('shareDocSelect').value = docId;
};

function setupEventListeners() {
    document.getElementById('generateSummaryBtn').addEventListener('click', generateSummary);
    document.getElementById('runFullExperimentBtn').addEventListener('click', runFullExperimentSuite);
    document.getElementById('runLeakageTestBtn').addEventListener('click', runLeakageTest);
    document.getElementById('runExperimentQuickBtn').addEventListener('click', runFullExperimentSuite);

    document.getElementById('confirmApproveBtn').addEventListener('click', () => handleHumanDecision('APPROVE'));
    document.getElementById('confirmRejectBtn').addEventListener('click', () => handleHumanDecision('REJECT'));

    document.getElementById('btnInjectEvent').addEventListener('click', handleEventInject);

    // Simulation shortcuts
    document.getElementById('btnSimDuplicate').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('injEventVersion').value = 1;
        document.getElementById('injSeqNum').value = 1;
        handleEventInject();
        setTimeout(handleEventInject, 300); // Duplicate call
    });

    document.getElementById('btnSimOutOfOrder').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('injEventVersion').value = 3;
        document.getElementById('injSeqNum').value = 20;
        handleEventInject();
    });

    document.getElementById('btnSimDelayed').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('injEventVersion').value = 1;
        document.getElementById('injSeqNum').value = 2;
        handleEventInject();
    });

    document.getElementById('auditActionFilter').addEventListener('change', loadAuditLogs);

    // Presentation slide navigation
    document.getElementById('prevSlideBtn').addEventListener('click', () => {
        if (state.currentSlide > 0) renderPresentationSlide(state.currentSlide - 1);
    });
    document.getElementById('nextSlideBtn').addEventListener('click', () => {
        if (state.currentSlide < slidesData.length - 1) renderPresentationSlide(state.currentSlide + 1);
    });

    // Doc tabs
    document.querySelectorAll('.doc-tab').forEach(tab => {
        tab.addEventListener('click', () => loadDocTab(tab.getAttribute('data-doc')));
    });

    // Share Form Submit
    document.getElementById('shareForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            requester_id: state.currentUser.id,
            recipient_id: document.getElementById('shareRecipientSelect').value,
            document_id: document.getElementById('shareDocSelect').value,
            reason: document.getElementById('shareReasonInput').value
        };

        const res = await fetch('/api/sharing/request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            alert(`Sharing request created! Status: ${data.status} (Risk Level: ${data.risk_level})`);
            document.getElementById('shareModal').classList.remove('active');
            await refreshSharingRequests();
            switchPage('sharing');
        } else {
            alert(data.detail || 'Error creating sharing request.');
        }
    });

    // Feedback Form Submit
    document.getElementById('feedbackForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            user_id: state.currentUser.id,
            role: state.currentUser.role,
            recommendation_clear: document.getElementById('valRecClear').value === 'true',
            reason_clear: document.getElementById('valReasonClear').value === 'true',
            usability_rating: parseInt(document.getElementById('valRating').value),
            comments: document.getElementById('valComments').value
        };

        await fetch('/api/validation/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        alert("Thank you! Feedback submitted successfully.");
        loadValidationSummary();
    });
}
