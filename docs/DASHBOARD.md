# VERION Dashboard

The VERION Dashboard is a comprehensive web-based user interface for managing and monitoring the Open Source HLR/HSS system. It provides real-time insights into system operations, subscriber management, charging, roaming, and network status.

## Overview

VERION Dashboard is automatically included with the HLR/HSS system and is accessible at:
```
http://localhost:8080/dashboard
```

![VERION Dashboard - Home](https://github.com/user-attachments/assets/62450535-112a-43f1-ac01-02f98baa68b0)

## Features

### 🏠 Home Section
- **System Overview** - View total subscribers, active sessions, system uptime, CPU and memory usage
- **Network Status** - Monitor Diameter, GSUP, and GTP interface status in real-time
- **Recent Alerts** - Track system events and warnings
- **Active Sessions Summary** - Quick view of current network activity

### 📊 Stats Section
- **Realtime Traffic** - Monitor throughput (Gbps), packets per second, active PDP/PDN contexts
- **Subscriber Counters** - View online subscribers by technology (2G/3G/4G/5G)
- **Cell/Node Load** - Track eNodeB and gNodeB load statistics
- **Transaction Rate** - Monitor Diameter and GSUP transactions per second
- **Usage by RAT** - Data usage breakdown by radio access technology
- **Historical Graphs** - View trends over day/week/month periods

### 📱 SIM Management Section
- **Subscriber List** - View all subscribers with pagination
- **Search** - Find subscribers by IMSI or MSISDN
- **Add Subscriber** - Create new subscriber profiles with authentication keys
- **Edit/Delete** - Modify or remove subscriber entries
- **Authentication Keys** - Manage KI and OPC values
- **Status Management** - View and update subscriber service status
- **Roaming Settings** - Configure roaming permissions per subscriber

![SIM Management](https://github.com/user-attachments/assets/7382df09-2bb5-41a9-9e64-0bf7dcb0e79b)

### 💰 OCS (Online Charging System) Section
- **Realtime Usage** - Monitor active charging sessions
- **Balance Management** - View subscriber balances and quotas
- **Tariff Profiles** - Manage data, SMS, and voice pricing
- **Event Logs** - Track Ro/Gy charging events
- **Policy Rules** - Configure Gx/PCRF policies
- **Quota Management** - Set and monitor usage limits

### 🌍 Roaming Section

#### Operators Tab
- **Partner List** - View roaming partners with MCC/MNC
- **Supported Technologies** - Track 2G/3G/4G/5G/VoLTE/VoNR support
- **Signaling Routes** - Manage Diameter realm configurations
- **Connection Status** - Monitor partner connectivity

#### Data Rates Tab
- **Roaming Tariff Table** - Configure pricing (€/MB, €/SMS, €/MIN)
- **Roaming Zones** - Manage EU/EEA/Global zone definitions
- **Preferred Partners** - Set routing preferences

#### Roaming Plans Tab
- **Plan List** - View plans like "Roam Like at Home", "Travel Data Pack"
- **Limits & Expiry** - Configure plan parameters
- **Linked Subscribers** - Track plan assignments

### 📡 Network Section

#### Diameter Peers Tab
- **Peer List** - View all Diameter connections (Host, Realm, App-ID)
- **Status Monitoring** - Real-time Up/Down status
- **Performance Metrics** - RTT and TPS per peer
- **Logs & Errors** - Troubleshoot connection issues

#### GSUP/MAP Peers Tab
- **2G/3G Core Connections** - Monitor legacy signaling
- **Status and Statistics** - Track connection health

#### GTP Sessions Tab
- **Active PDP/PDN Contexts** - View all active data sessions
- **Per-APN Throughput** - Monitor traffic by APN

#### Interface Configuration Tab
- **IP Bindings** - Configure S6a, Cx, Sh, GSUP interfaces
- **DRA Routing Rules** - Manage Diameter routing

### 🧾 Plans Section

#### Data Plans Tab
- **Plan List** - Manage plans like "Business Unlimited", "Prepaid 10GB"
- **QoS/QCI Mapping** - Configure quality of service parameters
- **Linked Subscribers** - View plan assignments

#### Voice & SMS Plans Tab
- **CSFB/IMS Rules** - Configure voice call settings
- **Voice Tariffs** - Set pricing for voice services

#### FWA/IoT Plans Tab
- **Static IP/NAT** - Configure fixed IP addresses
- **Private APN Rules** - Set up dedicated APNs
- **QCI/ARP Configs** - Define traffic priority

### 🧩 Configuration Section
- **System Settings** - Modify HLR/HSS parameters
- **Database Configuration** - View database connection status
- **Network Identity** - Check PLMN, MCC, MNC settings
- **Backup & Restore** - Manage system backups (future feature)
- **API Keys** - Manage external access credentials (future feature)

### 👥 Users & Access Section
- **Admin Accounts** - Manage administrator users
- **Operator Roles** - Configure user permissions
- **Login Audit Log** - Track authentication events
- **Session Management** - Monitor active user sessions

### 🧠 Tools Section

#### Ki/OPC Generator
- Generate cryptographically secure authentication keys
- One-click generation for subscriber provisioning

#### PLMN Lookup
- Look up network information by PLMN ID
- View MCC, MNC, operator name, and country

#### Network Test Console
- Ping tests (future feature)
- Diameter echo tests (future feature)
- Connectivity diagnostics (future feature)

## API Endpoints

The dashboard communicates with the backend through REST API endpoints:

### Home APIs
- `GET /dashboard/api/home/overview` - System overview data
- `GET /dashboard/api/home/network-status` - Network interface status
- `GET /dashboard/api/home/alerts` - Recent alerts

### Stats APIs
- `GET /dashboard/api/stats/realtime` - Real-time traffic statistics
- `GET /dashboard/api/stats/subscribers` - Subscriber counters by RAT
- `GET /dashboard/api/stats/cells` - Cell/node load statistics
- `GET /dashboard/api/stats/transactions` - Transaction rates
- `GET /dashboard/api/stats/usage-by-rat` - Data usage by technology
- `GET /dashboard/api/stats/graphs/{period}` - Historical data

### SIM Management APIs
- `GET /dashboard/api/sim/subscribers` - List subscribers (with pagination)
- `GET /dashboard/api/sim/subscriber/{imsi}` - Get subscriber details
- `POST /dashboard/api/sim/subscriber` - Create new subscriber
- `PUT /dashboard/api/sim/subscriber/{imsi}` - Update subscriber
- `DELETE /dashboard/api/sim/subscriber/{imsi}` - Delete subscriber

### OCS APIs
- `GET /dashboard/api/ocs/sessions` - Active charging sessions
- `GET /dashboard/api/ocs/balance/{imsi}` - Subscriber balance
- `GET /dashboard/api/ocs/tariffs` - Tariff profiles

### Roaming APIs
- `GET /dashboard/api/roaming/operators` - Roaming partners
- `GET /dashboard/api/roaming/rates` - Roaming rate tables
- `GET /dashboard/api/roaming/plans` - Roaming plans

### Network APIs
- `GET /dashboard/api/network/diameter-peers` - Diameter peer status
- `GET /dashboard/api/network/gtp-sessions` - Active GTP sessions
- `GET /dashboard/api/network/interfaces` - Network interface configuration

### Plans APIs
- `GET /dashboard/api/plans/data` - Data service plans
- `GET /dashboard/api/plans/voice` - Voice & SMS plans
- `GET /dashboard/api/plans/fwa` - FWA/IoT plans

### Configuration APIs
- `GET /dashboard/api/config/system` - System configuration

### Users APIs
- `GET /dashboard/api/users/admins` - Admin user accounts
- `GET /dashboard/api/users/audit` - Login audit log

### Tools APIs
- `GET /dashboard/api/tools/generate-ki` - Generate random KI
- `GET /dashboard/api/tools/generate-opc` - Generate random OPC
- `GET /dashboard/api/tools/plmn-lookup/{plmn_id}` - PLMN lookup

## Technical Details

### Architecture
- **Frontend**: Pure HTML5, CSS3, and vanilla JavaScript (no framework dependencies)
- **Backend**: Flask Blueprint integrated with main HLR/HSS application
- **API**: RESTful JSON APIs for all data operations
- **Real-time Updates**: Auto-refresh every 30 seconds
- **Responsive Design**: Mobile-friendly interface

### File Structure
```
hlr_hss/dashboard/
├── __init__.py
├── dashboard.py              # Flask Blueprint with API endpoints
├── static/
│   ├── css/
│   │   └── dashboard.css    # Styling
│   └── js/
│       └── dashboard.js     # Frontend logic
└── templates/
    └── dashboard.html       # Main template
```

### Security Considerations
- Dashboard should be deployed behind authentication in production
- Use HTTPS/TLS for all communications
- Implement role-based access control (RBAC)
- Regular security audits recommended
- Sensitive data (KI, OPC) should be masked in production

### Customization
The dashboard can be customized by:
- Modifying CSS in `static/css/dashboard.css`
- Extending JavaScript in `static/js/dashboard.js`
- Adding new API endpoints in `dashboard.py`
- Creating custom sections in `dashboard.html`

## Browser Compatibility
- Chrome/Edge (recommended): Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Responsive design supported

## Performance
- Lightweight: ~10KB CSS, ~40KB JavaScript (uncompressed)
- Fast loading: No external dependencies
- Efficient: API calls are optimized with pagination
- Scalable: Handles thousands of subscribers

## Future Enhancements
- WebSocket support for real-time push updates
- Export functionality (CSV, XML, JSON)
- Advanced filtering and sorting
- Custom dashboard widgets
- Multi-language support
- Dark mode theme
- Advanced analytics and reporting
- Grafana integration for advanced metrics

## Troubleshooting

### Dashboard not loading
- Verify the HLR/HSS application is running
- Check that port 8080 is accessible
- Ensure Flask and dependencies are installed

### Static files (CSS/JS) not loading
- Check blueprint static folder configuration
- Verify file permissions in `hlr_hss/dashboard/static/`
- Clear browser cache

### API errors
- Check application logs: `/tmp/hlr_hss.log`
- Verify database connection
- Check for proper initialization of OCS, DRA, and roaming components

### Data not displaying
- Open browser console (F12) to check for JavaScript errors
- Verify API endpoints are accessible
- Check network tab for failed requests

## Support
For issues related to the VERION Dashboard:
- GitHub Issues: https://github.com/Kaimeliax/Open-Source-HLR-HSS/issues
- Documentation: See main README.md

---

**Dashboard Version:** 1.0.0  
**Release Date:** 2025-10-24  
**Status:** Production Ready
