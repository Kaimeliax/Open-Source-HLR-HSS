// HLR/HSS Dashboard JavaScript

// API Base URL
const API_BASE_URL = '/api/v1';

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('HLR/HSS Dashboard initialized');
    
    // Check system health
    checkSystemHealth();
    
    // Load initial dashboard data
    loadDashboardData();
    
    // Set up form handlers
    setupFormHandlers();
    
    // Refresh dashboard every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// Show specific section and hide others
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Show selected section
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.style.display = 'block';
    }
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Load section-specific data
    switch(sectionName) {
        case 'subscribers':
            loadSubscribers();
            break;
        case 'ocs':
            loadOCSSessions();
            break;
        case 'roaming':
            loadRoamingPartners();
            break;
        case 'dashboard':
            loadDashboardData();
            break;
    }
}

// Check system health
async function checkSystemHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            document.getElementById('system-status').textContent = 'Healthy';
        } else {
            document.getElementById('system-status').textContent = 'Error';
        }
    } catch (error) {
        console.error('Health check failed:', error);
        document.getElementById('system-status').textContent = 'Error';
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load subscriber count
        const subscribersResponse = await fetch(`${API_BASE_URL}/subscribers`);
        if (subscribersResponse.ok) {
            const subscribersData = await subscribersResponse.json();
            document.getElementById('subscriber-count').textContent = subscribersData.count || 0;
        } else {
            document.getElementById('subscriber-count').textContent = 'N/A';
        }
    } catch (error) {
        console.error('Failed to load subscribers count:', error);
        document.getElementById('subscriber-count').textContent = 'N/A';
    }
    
    try {
        // Load OCS sessions count
        const ocsResponse = await fetch(`${API_BASE_URL}/ocs/sessions`);
        if (ocsResponse.ok) {
            const ocsData = await ocsResponse.json();
            document.getElementById('session-count').textContent = ocsData.count || 0;
        } else {
            document.getElementById('session-count').textContent = 'N/A';
        }
    } catch (error) {
        console.error('Failed to load OCS sessions:', error);
        document.getElementById('session-count').textContent = 'N/A';
    }
    
    try {
        // Load roaming partners count
        const roamingResponse = await fetch(`${API_BASE_URL}/roaming/partners`);
        if (roamingResponse.ok) {
            const roamingData = await roamingResponse.json();
            document.getElementById('partner-count').textContent = roamingData.count || 0;
        } else {
            document.getElementById('partner-count').textContent = 'N/A';
        }
    } catch (error) {
        console.error('Failed to load roaming partners:', error);
        document.getElementById('partner-count').textContent = 'N/A';
    }
}

// Load subscribers list
async function loadSubscribers() {
    try {
        const response = await fetch(`${API_BASE_URL}/subscribers`);
        const data = await response.json();
        
        const tbody = document.getElementById('subscribers-table-body');
        tbody.innerHTML = '';
        
        if (data.subscribers && data.subscribers.length > 0) {
            data.subscribers.forEach(subscriber => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${subscriber.imsi}</td>
                    <td>${subscriber.msisdn || 'N/A'}</td>
                    <td><span class="badge ${getStatusBadgeClass(subscriber.subscriber_status)}">${subscriber.subscriber_status || 'N/A'}</span></td>
                    <td>${subscriber.roaming_allowed ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-danger">No</span>'}</td>
                    <td>${subscriber.serving_mme || 'None'}</td>
                    <td>
                        <button class="btn btn-sm btn-info btn-action" onclick="viewSubscriber('${subscriber.imsi}')">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-danger btn-action" onclick="deleteSubscriber('${subscriber.imsi}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No subscribers found</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load subscribers:', error);
        showNotification('Failed to load subscribers', 'error');
        document.getElementById('subscribers-table-body').innerHTML = 
            '<tr><td colspan="6" class="text-center text-danger">Error loading subscribers</td></tr>';
    }
}

// Get status badge class
function getStatusBadgeClass(status) {
    switch(status) {
        case 'SERVICE_GRANTED':
            return 'bg-success';
        case 'OPERATOR_BARRING':
            return 'bg-warning';
        case 'SERVICE_NOT_ALLOWED':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

// View subscriber details
async function viewSubscriber(imsi) {
    try {
        const response = await fetch(`${API_BASE_URL}/subscribers/${imsi}`);
        const subscriber = await response.json();
        
        if (response.ok) {
            const details = `
                IMSI: ${subscriber.imsi}
                MSISDN: ${subscriber.msisdn}
                Status: ${subscriber.subscriber_status}
                Roaming: ${subscriber.roaming_allowed ? 'Yes' : 'No'}
                Serving MME: ${subscriber.serving_mme || 'None'}
                APNs: ${subscriber.apn_list ? subscriber.apn_list.join(', ') : 'None'}
            `;
            alert(details);
        } else {
            showNotification('Failed to load subscriber details', 'error');
        }
    } catch (error) {
        console.error('Failed to view subscriber:', error);
        showNotification('Failed to load subscriber details', 'error');
    }
}

// Delete subscriber
async function deleteSubscriber(imsi) {
    if (!confirm(`Are you sure you want to delete subscriber ${imsi}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/subscribers/${imsi}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Subscriber deleted successfully', 'success');
            loadSubscribers();
            loadDashboardData();
        } else {
            showNotification('Failed to delete subscriber', 'error');
        }
    } catch (error) {
        console.error('Failed to delete subscriber:', error);
        showNotification('Failed to delete subscriber', 'error');
    }
}

// Load OCS sessions
async function loadOCSSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/ocs/sessions`);
        const data = await response.json();
        
        const tbody = document.getElementById('ocs-sessions-table-body');
        tbody.innerHTML = '';
        
        if (response.ok && data.sessions && data.sessions.length > 0) {
            data.sessions.forEach(session => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${session.session_id}</td>
                    <td>${session.imsi}</td>
                    <td>$${session.current_balance ? session.current_balance.toFixed(2) : '0.00'}</td>
                    <td>${session.data_usage_bytes ? formatBytes(session.data_usage_bytes) : '0 B'}</td>
                    <td>
                        <button class="btn btn-sm btn-info btn-action" onclick="viewOCSSession('${session.session_id}')">
                            <i class="bi bi-eye"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        } else if (!response.ok && response.status === 501) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">OCS is not enabled</td></tr>';
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No active sessions</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load OCS sessions:', error);
        document.getElementById('ocs-sessions-table-body').innerHTML = 
            '<tr><td colspan="5" class="text-center text-danger">Error loading sessions</td></tr>';
    }
}

// View OCS session details
async function viewOCSSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/ocs/sessions/${sessionId}`);
        const session = await response.json();
        
        if (response.ok) {
            const details = `
                Session ID: ${session.session_id}
                IMSI: ${session.imsi}
                Current Balance: $${session.current_balance.toFixed(2)}
                Data Usage: ${formatBytes(session.data_usage_bytes)}
            `;
            alert(details);
        } else {
            showNotification('Failed to load session details', 'error');
        }
    } catch (error) {
        console.error('Failed to view session:', error);
        showNotification('Failed to load session details', 'error');
    }
}

// Load roaming partners
async function loadRoamingPartners() {
    try {
        const response = await fetch(`${API_BASE_URL}/roaming/partners`);
        const data = await response.json();
        
        const tbody = document.getElementById('roaming-partners-table-body');
        tbody.innerHTML = '';
        
        if (response.ok && data.partners && data.partners.length > 0) {
            data.partners.forEach(partner => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${partner.plmn_id}</td>
                    <td>${partner.partner_name}</td>
                    <td><span class="badge bg-info">${partner.roaming_type}</span></td>
                    <td><span class="badge ${partner.agreement_active ? 'bg-success' : 'bg-danger'}">
                        ${partner.agreement_active ? 'Active' : 'Inactive'}
                    </span></td>
                `;
                tbody.appendChild(row);
            });
        } else if (!response.ok && response.status === 501) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Roaming management is not enabled</td></tr>';
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No roaming partners configured</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load roaming partners:', error);
        document.getElementById('roaming-partners-table-body').innerHTML = 
            '<tr><td colspan="4" class="text-center text-danger">Error loading partners</td></tr>';
    }
}

// Setup form handlers
function setupFormHandlers() {
    // Add subscriber form
    const addSubscriberForm = document.getElementById('add-subscriber-form');
    if (addSubscriberForm) {
        addSubscriberForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const subscriberData = {
                msisdn: document.getElementById('msisdn').value,
                ki: document.getElementById('ki').value,
                opc: document.getElementById('opc').value,
                amf: document.getElementById('amf').value,
                subscriber_status: document.getElementById('status').value,
                roaming_allowed: document.getElementById('roaming').value === 'true'
            };
            
            const imsi = document.getElementById('imsi').value;
            
            try {
                const response = await fetch(`${API_BASE_URL}/subscribers/${imsi}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(subscriberData)
                });
                
                if (response.ok) {
                    showNotification('Subscriber added successfully', 'success');
                    addSubscriberForm.reset();
                    loadSubscribers();
                    loadDashboardData();
                } else {
                    const error = await response.json();
                    showNotification(`Failed to add subscriber: ${error.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                console.error('Failed to add subscriber:', error);
                showNotification('Failed to add subscriber', 'error');
            }
        });
    }
    
    // Auth vector form
    const authVectorForm = document.getElementById('auth-vector-form');
    if (authVectorForm) {
        authVectorForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const imsi = document.getElementById('auth-imsi').value;
            
            try {
                const response = await fetch(`${API_BASE_URL}/auth/${imsi}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const authVector = await response.json();
                    displayAuthVector(authVector);
                    showNotification('Authentication vector generated', 'success');
                } else {
                    const error = await response.json();
                    showNotification(`Failed to generate auth vector: ${error.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                console.error('Failed to generate auth vector:', error);
                showNotification('Failed to generate auth vector', 'error');
            }
        });
    }
}

// Display authentication vector
function displayAuthVector(authVector) {
    const resultDiv = document.getElementById('auth-vector-result');
    
    let html = '<div class="code-block">';
    
    for (const [key, value] of Object.entries(authVector)) {
        html += `
            <div class="mb-2">
                <span class="code-label">${key.toUpperCase()}:</span>
                <span class="code-value">${value}</span>
            </div>
        `;
    }
    
    html += '</div>';
    resultDiv.innerHTML = html;
}

// Format bytes to human readable
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Show notification toast
function showNotification(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const toastMessage = document.getElementById('toast-message');
    const toastHeader = toast.querySelector('.toast-header');
    
    // Set message
    toastMessage.textContent = message;
    
    // Set color based on type
    toastHeader.classList.remove('bg-success', 'bg-danger', 'bg-info', 'bg-warning', 'text-white');
    if (type === 'success') {
        toastHeader.classList.add('bg-success', 'text-white');
    } else if (type === 'error') {
        toastHeader.classList.add('bg-danger', 'text-white');
    } else if (type === 'warning') {
        toastHeader.classList.add('bg-warning');
    } else {
        toastHeader.classList.add('bg-info', 'text-white');
    }
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}
