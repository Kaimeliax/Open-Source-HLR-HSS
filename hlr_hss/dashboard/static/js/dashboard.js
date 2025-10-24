// VERION Dashboard - Main JavaScript

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupNavigation();
    setupTabs();
    loadHomeSection();
    
    // Auto-refresh every 30 seconds
    setInterval(() => {
        const activeSection = document.querySelector('.content-section.active');
        if (activeSection) {
            const sectionId = activeSection.id.replace('section-', '');
            loadSection(sectionId);
        }
    }, 30000);
});

// Initialize dashboard
function initializeDashboard() {
    console.log('VERION Dashboard initialized');
}

// Setup navigation
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Get section name
            const section = this.dataset.section;
            
            // Update header title
            const titles = {
                'home': 'System Overview',
                'stats': 'Statistics',
                'sim': 'SIM Management',
                'ocs': 'Online Charging System',
                'roaming': 'Roaming Management',
                'network': 'Network Status',
                'plans': 'Service Plans',
                'config': 'Configuration',
                'users': 'Users & Access',
                'tools': 'Tools'
            };
            document.getElementById('section-title').textContent = titles[section] || section;
            
            // Show section
            showSection(section);
            
            // Load section data
            loadSection(section);
        });
    });
}

// Show section
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const section = document.getElementById('section-' + sectionName);
    if (section) {
        section.classList.add('active');
    }
}

// Load section data
function loadSection(sectionName) {
    switch(sectionName) {
        case 'home':
            loadHomeSection();
            break;
        case 'stats':
            loadStatsSection();
            break;
        case 'sim':
            loadSimSection();
            break;
        case 'ocs':
            loadOcsSection();
            break;
        case 'roaming':
            loadRoamingSection();
            break;
        case 'network':
            loadNetworkSection();
            break;
        case 'plans':
            loadPlansSection();
            break;
        case 'config':
            loadConfigSection();
            break;
        case 'users':
            loadUsersSection();
            break;
        case 'tools':
            // Tools section is static, no loading needed
            break;
    }
}

// Refresh current section
function refreshCurrentSection() {
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection) {
        const sectionId = activeSection.id.replace('section-', '');
        loadSection(sectionId);
    }
}

// ==================== Home Section ====================
function loadHomeSection() {
    fetch('/dashboard/api/home/overview')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-subscribers').textContent = data.subscribers_total;
            document.getElementById('active-sessions').textContent = data.active_sessions;
            document.getElementById('system-uptime').textContent = data.system_uptime;
            document.getElementById('cpu-usage').textContent = data.cpu_usage + '%';
            document.getElementById('memory-usage').textContent = data.memory_usage + '%';
        })
        .catch(error => console.error('Error loading overview:', error));
    
    fetch('/dashboard/api/home/network-status')
        .then(response => response.json())
        .then(data => {
            updateNetworkStatus('diameter', data.diameter);
            updateNetworkStatus('gsup', data.gsup);
            updateNetworkStatus('gtp', data.gtp);
        })
        .catch(error => console.error('Error loading network status:', error));
    
    fetch('/dashboard/api/home/alerts')
        .then(response => response.json())
        .then(data => {
            const alertsList = document.getElementById('alerts-list');
            if (data.alerts && data.alerts.length > 0) {
                alertsList.innerHTML = data.alerts.map(alert => `
                    <div class="alert-item ${alert.level}">
                        <div class="alert-message">${alert.message}</div>
                        <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                    </div>
                `).join('');
            } else {
                alertsList.innerHTML = '<p>No recent alerts</p>';
            }
        })
        .catch(error => console.error('Error loading alerts:', error));
}

function updateNetworkStatus(type, data) {
    const statusBadge = document.getElementById(type + '-status');
    const statusDetail = document.getElementById(type + '-detail');
    
    statusBadge.textContent = data.status;
    statusBadge.className = 'status-badge ' + data.status;
    
    let detail = '';
    if (type === 'diameter') {
        detail = `${data.peers_connected}/${data.peers_total} peers, ${data.messages_per_sec} msg/s`;
    } else if (type === 'gsup') {
        detail = `${data.connections} connections, ${data.messages_per_sec} msg/s`;
    } else if (type === 'gtp') {
        detail = `${data.active_tunnels} tunnels, ${data.throughput_mbps} Mbps`;
    }
    statusDetail.textContent = detail;
}

// ==================== Stats Section ====================
function loadStatsSection() {
    fetch('/dashboard/api/stats/realtime')
        .then(response => response.json())
        .then(data => {
            document.getElementById('realtime-traffic').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Throughput:</span>
                    <span class="stat-value">${data.throughput_gbps} Gbps</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Packets/sec:</span>
                    <span class="stat-value">${data.packets_per_sec.toLocaleString()}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Active PDP/PDN:</span>
                    <span class="stat-value">${data.active_pdp_pdn}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Latency:</span>
                    <span class="stat-value">${data.latency_ms} ms</span>
                </div>
            `;
        })
        .catch(error => console.error('Error loading realtime stats:', error));
    
    fetch('/dashboard/api/stats/subscribers')
        .then(response => response.json())
        .then(data => {
            document.getElementById('subscribers-by-rat').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">2G Online:</span>
                    <span class="stat-value">${data['2g_online']}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">3G Online:</span>
                    <span class="stat-value">${data['3g_online']}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">4G Online:</span>
                    <span class="stat-value">${data['4g_online']}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">5G Online:</span>
                    <span class="stat-value">${data['5g_online']}</span>
                </div>
            `;
        })
        .catch(error => console.error('Error loading subscriber stats:', error));
    
    fetch('/dashboard/api/stats/cells')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cell-load').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">eNodeB Count:</span>
                    <span class="stat-value">${data.enodeb_count}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">gNodeB Count:</span>
                    <span class="stat-value">${data.gnodeb_count}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Avg Load:</span>
                    <span class="stat-value">${data.avg_load_percent}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Overloaded:</span>
                    <span class="stat-value">${data.overloaded_cells}</span>
                </div>
            `;
        })
        .catch(error => console.error('Error loading cell stats:', error));
    
    fetch('/dashboard/api/stats/transactions')
        .then(response => response.json())
        .then(data => {
            document.getElementById('transaction-rate').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Diameter TPS:</span>
                    <span class="stat-value">${data.diameter_tps}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">GSUP TPS:</span>
                    <span class="stat-value">${data.gsup_tps}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Total TPS:</span>
                    <span class="stat-value">${data.total_tps}</span>
                </div>
            `;
        })
        .catch(error => console.error('Error loading transaction stats:', error));
    
    fetch('/dashboard/api/stats/usage-by-rat')
        .then(response => response.json())
        .then(data => {
            document.getElementById('usage-by-rat').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">2G:</span>
                    <span class="stat-value">${data['2g'].data_gb} GB (${data['2g'].percentage}%)</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">3G:</span>
                    <span class="stat-value">${data['3g'].data_gb} GB (${data['3g'].percentage}%)</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">4G:</span>
                    <span class="stat-value">${data['4g'].data_gb} GB (${data['4g'].percentage}%)</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">5G:</span>
                    <span class="stat-value">${data['5g'].data_gb} GB (${data['5g'].percentage}%)</span>
                </div>
            `;
        })
        .catch(error => console.error('Error loading usage stats:', error));
}

// ==================== SIM Management Section ====================
function loadSimSection() {
    loadSubscribers();
    
    // Setup search
    const searchBox = document.getElementById('sim-search');
    if (searchBox) {
        searchBox.addEventListener('input', debounce(function() {
            loadSubscribers(1, this.value);
        }, 500));
    }
}

function loadSubscribers(page = 1, search = '') {
    const url = `/dashboard/api/sim/subscribers?page=${page}&per_page=20&search=${encodeURIComponent(search)}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('subscribers-table-body');
            
            if (data.subscribers && data.subscribers.length > 0) {
                tbody.innerHTML = data.subscribers.map(sub => `
                    <tr>
                        <td>${sub.imsi || 'N/A'}</td>
                        <td>${sub.msisdn || 'N/A'}</td>
                        <td>${sub.subscriber_status || 'N/A'}</td>
                        <td>${sub.roaming_allowed ? '✓' : '✗'}</td>
                        <td>
                            <button class="btn-secondary" onclick="viewSubscriber('${sub.imsi}')">View</button>
                            <button class="btn-danger" onclick="deleteSubscriber('${sub.imsi}')">Delete</button>
                        </td>
                    </tr>
                `).join('');
                
                // Update pagination
                updatePagination('subscribers-pagination', page, data.total_pages, (newPage) => loadSubscribers(newPage, search));
            } else {
                tbody.innerHTML = '<tr><td colspan="5" class="loading">No subscribers found</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading subscribers:', error);
            document.getElementById('subscribers-table-body').innerHTML = '<tr><td colspan="5" class="loading">Error loading subscribers</td></tr>';
        });
}

function viewSubscriber(imsi) {
    alert('View subscriber: ' + imsi + '\n(Detailed view to be implemented)');
}

function deleteSubscriber(imsi) {
    if (!confirm('Delete subscriber ' + imsi + '?')) return;
    
    fetch(`/dashboard/api/sim/subscriber/${imsi}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            alert(data.message || 'Subscriber deleted');
            loadSubscribers();
        })
        .catch(error => {
            console.error('Error deleting subscriber:', error);
            alert('Error deleting subscriber');
        });
}

// ==================== OCS Section ====================
function loadOcsSection() {
    fetch('/dashboard/api/ocs/sessions')
        .then(response => response.json())
        .then(data => {
            const sessionsDiv = document.getElementById('ocs-sessions');
            if (data.sessions && data.sessions.length > 0) {
                sessionsDiv.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Session ID</th>
                                <th>IMSI</th>
                                <th>Balance</th>
                                <th>Data Usage</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.sessions.map(s => `
                                <tr>
                                    <td>${s.session_id}</td>
                                    <td>${s.imsi}</td>
                                    <td>$${s.current_balance.toFixed(2)}</td>
                                    <td>${s.data_usage_mb} MB</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                sessionsDiv.innerHTML = '<p>No active sessions</p>';
            }
        })
        .catch(error => console.error('Error loading OCS sessions:', error));
    
    fetch('/dashboard/api/ocs/tariffs')
        .then(response => response.json())
        .then(data => {
            const tariffsDiv = document.getElementById('ocs-tariffs');
            tariffsDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Data ($/MB)</th>
                            <th>Voice ($/min)</th>
                            <th>SMS ($/msg)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.tariffs.map(t => `
                            <tr>
                                <td>${t.name}</td>
                                <td>$${t.data_per_mb.toFixed(3)}</td>
                                <td>$${t.voice_per_min.toFixed(2)}</td>
                                <td>$${t.sms_per_msg.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading OCS tariffs:', error));
}

// ==================== Roaming Section ====================
function loadRoamingSection() {
    loadRoamingOperators();
    loadRoamingRates();
    loadRoamingPlans();
}

function loadRoamingOperators() {
    fetch('/dashboard/api/roaming/operators')
        .then(response => response.json())
        .then(data => {
            const operatorsDiv = document.getElementById('roaming-operators');
            if (data.partners && data.partners.length > 0) {
                operatorsDiv.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>PLMN ID</th>
                                <th>Operator</th>
                                <th>Country</th>
                                <th>Type</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.partners.map(p => `
                                <tr>
                                    <td>${p.plmn_id}</td>
                                    <td>${p.partner_name}</td>
                                    <td>${p.country_code}</td>
                                    <td>${p.roaming_type}</td>
                                    <td>${p.agreement_active ? '✓ Active' : '✗ Inactive'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                operatorsDiv.innerHTML = '<p>No roaming partners configured</p>';
            }
        })
        .catch(error => console.error('Error loading roaming operators:', error));
}

function loadRoamingRates() {
    fetch('/dashboard/api/roaming/rates')
        .then(response => response.json())
        .then(data => {
            const ratesDiv = document.getElementById('roaming-rates');
            ratesDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Zone</th>
                            <th>Data (€/MB)</th>
                            <th>Voice (€/min)</th>
                            <th>SMS (€/msg)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.zones.map(z => `
                            <tr>
                                <td>${z.zone}</td>
                                <td>€${z.data_per_mb.toFixed(2)}</td>
                                <td>€${z.voice_per_min.toFixed(2)}</td>
                                <td>€${z.sms_per_msg.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading roaming rates:', error));
}

function loadRoamingPlans() {
    fetch('/dashboard/api/roaming/plans')
        .then(response => response.json())
        .then(data => {
            const plansDiv = document.getElementById('roaming-plans');
            plansDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Plan Name</th>
                            <th>Data Limit</th>
                            <th>Expiry</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.plans.map(p => `
                            <tr>
                                <td>${p.name}</td>
                                <td>${p.data_limit_mb === 'unlimited' ? 'Unlimited' : p.data_limit_mb + ' MB'}</td>
                                <td>${p.expiry_days} days</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading roaming plans:', error));
}

// ==================== Network Section ====================
function loadNetworkSection() {
    loadDiameterPeers();
    loadGtpSessions();
    loadNetworkInterfaces();
}

function loadDiameterPeers() {
    fetch('/dashboard/api/network/diameter-peers')
        .then(response => response.json())
        .then(data => {
            const peersDiv = document.getElementById('diameter-peers');
            if (data.peers && data.peers.length > 0) {
                peersDiv.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Host</th>
                                <th>Realm</th>
                                <th>Application</th>
                                <th>Status</th>
                                <th>RTT</th>
                                <th>TPS</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.peers.map(p => `
                                <tr>
                                    <td>${p.host}</td>
                                    <td>${p.realm}</td>
                                    <td>${p.app_id}</td>
                                    <td><span class="status-badge ${p.status}">${p.status}</span></td>
                                    <td>${p.rtt_ms} ms</td>
                                    <td>${p.tps}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                peersDiv.innerHTML = '<p>No diameter peers configured</p>';
            }
        })
        .catch(error => console.error('Error loading diameter peers:', error));
}

function loadGtpSessions() {
    fetch('/dashboard/api/network/gtp-sessions')
        .then(response => response.json())
        .then(data => {
            const sessionsDiv = document.getElementById('gtp-sessions');
            if (data.sessions && data.sessions.length > 0) {
                sessionsDiv.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>IMSI</th>
                                <th>APN</th>
                                <th>IP Address</th>
                                <th>Throughput</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.sessions.map(s => `
                                <tr>
                                    <td>${s.imsi}</td>
                                    <td>${s.apn}</td>
                                    <td>${s.ip}</td>
                                    <td>${s.throughput_kbps} kbps</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            } else {
                sessionsDiv.innerHTML = '<p>No active GTP sessions</p>';
            }
        })
        .catch(error => console.error('Error loading GTP sessions:', error));
}

function loadNetworkInterfaces() {
    fetch('/dashboard/api/network/interfaces')
        .then(response => response.json())
        .then(data => {
            const interfacesDiv = document.getElementById('network-interfaces');
            interfacesDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Interface</th>
                            <th>Bind IP</th>
                            <th>Port</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.interfaces.map(i => `
                            <tr>
                                <td>${i.name}</td>
                                <td>${i.bind_ip}</td>
                                <td>${i.port}</td>
                                <td><span class="status-badge ${i.status}">${i.status}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading network interfaces:', error));
}

// ==================== Plans Section ====================
function loadPlansSection() {
    loadDataPlans();
    loadVoicePlans();
    loadFwaPlans();
}

function loadDataPlans() {
    fetch('/dashboard/api/plans/data')
        .then(response => response.json())
        .then(data => {
            const plansDiv = document.getElementById('data-plans');
            plansDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Data Limit</th>
                            <th>QCI</th>
                            <th>ARP</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.plans.map(p => `
                            <tr>
                                <td>${p.name}</td>
                                <td>${p.data_limit}</td>
                                <td>${p.qci}</td>
                                <td>${p.arp}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading data plans:', error));
}

function loadVoicePlans() {
    fetch('/dashboard/api/plans/voice')
        .then(response => response.json())
        .then(data => {
            const plansDiv = document.getElementById('voice-plans');
            plansDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Minutes</th>
                            <th>SMS</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.plans.map(p => `
                            <tr>
                                <td>${p.name}</td>
                                <td>${p.minutes === 'unlimited' ? 'Unlimited' : p.minutes}</td>
                                <td>${p.sms === 'unlimited' ? 'Unlimited' : p.sms}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading voice plans:', error));
}

function loadFwaPlans() {
    fetch('/dashboard/api/plans/fwa')
        .then(response => response.json())
        .then(data => {
            const plansDiv = document.getElementById('fwa-plans');
            plansDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Static IP</th>
                            <th>QCI</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.plans.map(p => `
                            <tr>
                                <td>${p.name}</td>
                                <td>${p.type}</td>
                                <td>${p.static_ip ? '✓' : '✗'}</td>
                                <td>${p.qci}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading FWA plans:', error));
}

// ==================== Configuration Section ====================
function loadConfigSection() {
    fetch('/dashboard/api/config/system')
        .then(response => response.json())
        .then(data => {
            const configDiv = document.getElementById('system-config');
            configDiv.innerHTML = `
                <h4>Network Configuration</h4>
                <div class="stat-item">
                    <span class="stat-label">PLMN ID:</span>
                    <span class="stat-value">${data.network.plmn_id}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">MCC:</span>
                    <span class="stat-value">${data.network.mcc}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">MNC:</span>
                    <span class="stat-value">${data.network.mnc}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Network Name:</span>
                    <span class="stat-value">${data.network.network_name}</span>
                </div>
                <h4 style="margin-top: 20px;">Database</h4>
                <div class="stat-item">
                    <span class="stat-label">Type:</span>
                    <span class="stat-value">${data.database.type}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value">${data.database.status}</span>
                </div>
            `;
        })
        .catch(error => console.error('Error loading config:', error));
}

// ==================== Users Section ====================
function loadUsersSection() {
    fetch('/dashboard/api/users/admins')
        .then(response => response.json())
        .then(data => {
            const adminsDiv = document.getElementById('admin-accounts');
            adminsDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Role</th>
                            <th>Last Login</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.users.map(u => `
                            <tr>
                                <td>${u.username}</td>
                                <td>${u.role}</td>
                                <td>${new Date(u.last_login).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading admin accounts:', error));
    
    fetch('/dashboard/api/users/audit')
        .then(response => response.json())
        .then(data => {
            const auditDiv = document.getElementById('audit-log');
            auditDiv.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Action</th>
                            <th>IP Address</th>
                            <th>Timestamp</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.logs.map(l => `
                            <tr>
                                <td>${l.username}</td>
                                <td>${l.action}</td>
                                <td>${l.ip}</td>
                                <td>${new Date(l.timestamp).toLocaleString()}</td>
                                <td>${l.success ? '✓' : '✗'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        })
        .catch(error => console.error('Error loading audit log:', error));
}

// ==================== Tools Section ====================
function generateKi() {
    fetch('/dashboard/api/tools/generate-ki')
        .then(response => response.json())
        .then(data => {
            document.getElementById('generated-ki').textContent = 'KI: ' + data.ki;
        })
        .catch(error => console.error('Error generating KI:', error));
}

function generateOpc() {
    fetch('/dashboard/api/tools/generate-opc')
        .then(response => response.json())
        .then(data => {
            document.getElementById('generated-opc').textContent = 'OPC: ' + data.opc;
        })
        .catch(error => console.error('Error generating OPC:', error));
}

function lookupPlmn() {
    const plmnId = document.getElementById('plmn-input').value;
    if (!plmnId) {
        alert('Please enter a PLMN ID');
        return;
    }
    
    fetch(`/dashboard/api/tools/plmn-lookup/${plmnId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('plmn-result').innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">MCC:</span>
                    <span class="stat-value">${data.mcc}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">MNC:</span>
                    <span class="stat-value">${data.mnc}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Network:</span>
                    <span class="stat-value">${data.network}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Country:</span>
                    <span class="stat-value">${data.country}</span>
                </div>
            `;
        })
        .catch(error => console.error('Error looking up PLMN:', error));
}

// ==================== Modal Functions ====================
function showAddSubscriberModal() {
    document.getElementById('add-subscriber-modal').classList.add('show');
}

function closeAddSubscriberModal() {
    document.getElementById('add-subscriber-modal').classList.remove('show');
    document.getElementById('add-subscriber-form').reset();
}

function submitAddSubscriber(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        imsi: formData.get('imsi'),
        msisdn: formData.get('msisdn'),
        ki: formData.get('ki'),
        opc: formData.get('opc'),
        roaming_allowed: formData.get('roaming_allowed') === 'on'
    };
    
    fetch('/dashboard/api/sim/subscriber', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        alert(result.message || 'Subscriber added');
        closeAddSubscriberModal();
        loadSubscribers();
    })
    .catch(error => {
        console.error('Error adding subscriber:', error);
        alert('Error adding subscriber');
    });
}

// ==================== Tabs Setup ====================
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            const parent = this.closest('section');
            
            // Remove active class from all tab buttons in this section
            parent.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Hide all tab panes in this section
            parent.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            // Show selected tab pane
            const selectedPane = parent.querySelector(`#tab-${tabName}`);
            if (selectedPane) {
                selectedPane.classList.add('active');
            }
        });
    });
}

// ==================== Utility Functions ====================
function updatePagination(containerId, currentPage, totalPages, callback) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '';
    
    if (currentPage > 1) {
        html += `<button onclick="(${callback})(${currentPage - 1})">Previous</button>`;
    }
    
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        const activeClass = i === currentPage ? ' active' : '';
        html += `<button class="${activeClass}" onclick="(${callback})(${i})">${i}</button>`;
    }
    
    if (currentPage < totalPages) {
        html += `<button onclick="(${callback})(${currentPage + 1})">Next</button>`;
    }
    
    container.innerHTML = html;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
