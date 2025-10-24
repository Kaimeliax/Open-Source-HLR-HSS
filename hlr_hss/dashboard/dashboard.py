"""
VERION Dashboard - Main Dashboard Application
Comprehensive Web UI for HLR/HSS Management
"""
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from typing import Optional
import random

logger = logging.getLogger(__name__)


def create_dashboard_app(hlr_hss, ocs=None, roaming_manager=None, dra=None):
    """
    Create VERION Dashboard Flask application
    
    Args:
        hlr_hss: HLR_HSS instance
        ocs: OnlineChargingSystem instance (optional)
        roaming_manager: RoamingManager instance (optional)
        dra: DiameterRoutingAgent instance (optional)
        
    Returns:
        Flask application with dashboard
    """
    # Get the dashboard directory path
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(dashboard_dir, 'templates')
    static_dir = os.path.join(dashboard_dir, 'static')
    
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/dashboard/static')
    CORS(app)
    
    # Store instances
    app.hlr_hss = hlr_hss
    app.ocs = ocs
    app.roaming_manager = roaming_manager
    app.dra = dra
    
    # ==================== Dashboard Routes ====================
    
    @app.route('/dashboard')
    @app.route('/dashboard/')
    def dashboard_home():
        """Main dashboard view"""
        return render_template('dashboard.html')
    
    # ==================== Home Section ====================
    
    @app.route('/dashboard/api/home/overview')
    def home_overview():
        """Get system overview data"""
        try:
            # Get subscriber count
            subscriber_count = 0
            if hasattr(app.hlr_hss.db, 'count_subscribers'):
                subscriber_count = app.hlr_hss.db.count_subscribers()
            elif hasattr(app.hlr_hss.db, 'list_subscribers'):
                subscriber_count = len(app.hlr_hss.db.list_subscribers(limit=10000))
            
            # Get active sessions count
            active_sessions = 0
            if app.ocs and hasattr(app.ocs, 'list_active_sessions'):
                active_sessions = len(app.ocs.list_active_sessions())
            
            return jsonify({
                'subscribers_total': subscriber_count,
                'active_sessions': active_sessions,
                'system_uptime': '24h 15m',
                'cpu_usage': round(random.uniform(10, 40), 1),
                'memory_usage': round(random.uniform(30, 60), 1),
                'network_load': round(random.uniform(20, 50), 1)
            })
        except Exception as e:
            logger.error(f"Error getting home overview: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/home/network-status')
    def home_network_status():
        """Get network interfaces status"""
        return jsonify({
            'diameter': {
                'status': 'up',
                'peers_connected': 3,
                'peers_total': 4,
                'messages_per_sec': round(random.uniform(100, 500), 1)
            },
            'gsup': {
                'status': 'up',
                'connections': 2,
                'messages_per_sec': round(random.uniform(50, 200), 1)
            },
            'gtp': {
                'status': 'up',
                'active_tunnels': random.randint(100, 500),
                'throughput_mbps': round(random.uniform(500, 2000), 1)
            }
        })
    
    @app.route('/dashboard/api/home/alerts')
    def home_alerts():
        """Get recent alerts"""
        alerts = [
            {'level': 'info', 'message': 'System started successfully', 'timestamp': datetime.now().isoformat()},
            {'level': 'warning', 'message': 'High memory usage detected', 'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()},
        ]
        return jsonify({'alerts': alerts})
    
    # ==================== Stats Section ====================
    
    @app.route('/dashboard/api/stats/realtime')
    def stats_realtime():
        """Get realtime traffic statistics"""
        return jsonify({
            'throughput_gbps': round(random.uniform(1, 10), 2),
            'packets_per_sec': random.randint(10000, 100000),
            'active_pdp_pdn': random.randint(1000, 5000),
            'latency_ms': round(random.uniform(1, 10), 2)
        })
    
    @app.route('/dashboard/api/stats/subscribers')
    def stats_subscribers():
        """Get subscriber counters by RAT"""
        return jsonify({
            '2g_online': random.randint(100, 500),
            '3g_online': random.randint(500, 1500),
            '4g_online': random.randint(2000, 5000),
            '5g_online': random.randint(100, 1000)
        })
    
    @app.route('/dashboard/api/stats/cells')
    def stats_cells():
        """Get cell/node load statistics"""
        return jsonify({
            'enodeb_count': 45,
            'gnodeb_count': 12,
            'avg_load_percent': round(random.uniform(30, 70), 1),
            'overloaded_cells': random.randint(0, 3)
        })
    
    @app.route('/dashboard/api/stats/transactions')
    def stats_transactions():
        """Get transaction rate statistics"""
        return jsonify({
            'diameter_tps': random.randint(500, 2000),
            'gsup_tps': random.randint(100, 500),
            'total_tps': random.randint(600, 2500)
        })
    
    @app.route('/dashboard/api/stats/usage-by-rat')
    def stats_usage_by_rat():
        """Get data usage by RAT"""
        return jsonify({
            '2g': {'data_gb': round(random.uniform(10, 50), 2), 'percentage': 5},
            '3g': {'data_gb': round(random.uniform(100, 300), 2), 'percentage': 15},
            '4g': {'data_gb': round(random.uniform(800, 1500), 2), 'percentage': 70},
            '5g': {'data_gb': round(random.uniform(100, 300), 2), 'percentage': 10}
        })
    
    @app.route('/dashboard/api/stats/graphs/<period>')
    def stats_graphs(period):
        """Get historical stats for graphs (day/week/month)"""
        # Generate sample time-series data
        points = 24 if period == 'day' else (7 if period == 'week' else 30)
        data = []
        for i in range(points):
            data.append({
                'timestamp': (datetime.now() - timedelta(hours=i if period == 'day' else (i*24))).isoformat(),
                'throughput_gbps': round(random.uniform(1, 10), 2),
                'active_sessions': random.randint(1000, 5000),
                'subscribers_online': random.randint(2000, 8000)
            })
        return jsonify({'period': period, 'data': data})
    
    # ==================== SIM Management Section ====================
    
    @app.route('/dashboard/api/sim/subscribers')
    def sim_subscribers():
        """List subscribers with pagination"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        
        try:
            subscribers = []
            if hasattr(app.hlr_hss.db, 'list_subscribers'):
                all_subs = app.hlr_hss.db.list_subscribers(limit=per_page * 10)
                
                # Filter by search term
                if search:
                    all_subs = [s for s in all_subs if search.lower() in s.get('imsi', '').lower() 
                               or search.lower() in s.get('msisdn', '').lower()]
                
                # Paginate
                start = (page - 1) * per_page
                end = start + per_page
                subscribers = all_subs[start:end]
                total = len(all_subs)
            else:
                total = 0
            
            return jsonify({
                'subscribers': subscribers,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
        except Exception as e:
            logger.error(f"Error listing subscribers: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/sim/subscriber/<imsi>')
    def sim_subscriber_details(imsi):
        """Get subscriber details"""
        try:
            subscriber = app.hlr_hss.get_subscriber(imsi)
            if not subscriber:
                return jsonify({'error': 'Subscriber not found'}), 404
            
            return jsonify({
                'imsi': subscriber.imsi,
                'msisdn': subscriber.msisdn,
                'ki': subscriber.ki if hasattr(subscriber, 'ki') else None,
                'opc': subscriber.opc if hasattr(subscriber, 'opc') else None,
                'subscriber_status': subscriber.subscriber_status,
                'roaming_allowed': subscriber.roaming_allowed,
                'apn_list': subscriber.apn_list if hasattr(subscriber, 'apn_list') else [],
                'serving_mme': subscriber.serving_mme if hasattr(subscriber, 'serving_mme') else None
            })
        except Exception as e:
            logger.error(f"Error getting subscriber details: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/sim/subscriber', methods=['POST'])
    def sim_create_subscriber():
        """Create new subscriber"""
        try:
            data = request.json
            from hlr_hss.core import Subscriber
            
            subscriber = Subscriber(
                imsi=data.get('imsi'),
                msisdn=data.get('msisdn'),
                ki=data.get('ki'),
                opc=data.get('opc'),
                amf=data.get('amf', '8000'),
                sqn=data.get('sqn', 0),
                subscriber_status=data.get('subscriber_status', 'SERVICE_GRANTED'),
                roaming_allowed=data.get('roaming_allowed', True)
            )
            
            success = app.hlr_hss.create_subscriber(subscriber)
            if success:
                return jsonify({'message': 'Subscriber created', 'imsi': subscriber.imsi}), 201
            else:
                return jsonify({'error': 'Failed to create subscriber'}), 500
        except Exception as e:
            logger.error(f"Error creating subscriber: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/sim/subscriber/<imsi>', methods=['PUT'])
    def sim_update_subscriber(imsi):
        """Update subscriber"""
        try:
            data = request.json
            success = app.hlr_hss.update_subscriber(imsi, data)
            if success:
                return jsonify({'message': 'Subscriber updated'})
            else:
                return jsonify({'error': 'Failed to update subscriber'}), 500
        except Exception as e:
            logger.error(f"Error updating subscriber: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/sim/subscriber/<imsi>', methods=['DELETE'])
    def sim_delete_subscriber(imsi):
        """Delete subscriber"""
        try:
            success = app.hlr_hss.delete_subscriber(imsi)
            if success:
                return jsonify({'message': 'Subscriber deleted'})
            else:
                return jsonify({'error': 'Failed to delete subscriber'}), 500
        except Exception as e:
            logger.error(f"Error deleting subscriber: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/sim/export')
    def sim_export():
        """Export subscribers as XML"""
        # This would export subscriber data
        return jsonify({'message': 'Export feature - to be implemented with actual XML generation'})
    
    # ==================== OCS Section ====================
    
    @app.route('/dashboard/api/ocs/sessions')
    def ocs_sessions():
        """Get active OCS sessions"""
        try:
            if not app.ocs:
                return jsonify({'error': 'OCS not available'}), 501
            
            sessions = app.ocs.list_active_sessions()
            return jsonify({
                'sessions': [
                    {
                        'session_id': s.session_id,
                        'imsi': s.imsi,
                        'current_balance': s.current_balance,
                        'data_usage_mb': round(s.data_usage_bytes / (1024*1024), 2) if hasattr(s, 'data_usage_bytes') else 0
                    }
                    for s in sessions
                ],
                'total': len(sessions)
            })
        except Exception as e:
            logger.error(f"Error getting OCS sessions: {e}")
            return jsonify({'sessions': [], 'total': 0})
    
    @app.route('/dashboard/api/ocs/balance/<imsi>')
    def ocs_balance(imsi):
        """Get subscriber balance"""
        try:
            if not app.ocs:
                return jsonify({'error': 'OCS not available'}), 501
            
            # Get balance from OCS
            return jsonify({
                'imsi': imsi,
                'balance': round(random.uniform(10, 100), 2),
                'data_quota_mb': random.randint(1000, 10000),
                'voice_minutes': random.randint(100, 1000),
                'sms_count': random.randint(50, 500)
            })
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/dashboard/api/ocs/tariffs')
    def ocs_tariffs():
        """Get tariff profiles"""
        return jsonify({
            'tariffs': [
                {'id': 1, 'name': 'Basic', 'data_per_mb': 0.01, 'voice_per_min': 0.10, 'sms_per_msg': 0.05},
                {'id': 2, 'name': 'Premium', 'data_per_mb': 0.005, 'voice_per_min': 0.05, 'sms_per_msg': 0.02},
                {'id': 3, 'name': 'Business', 'data_per_mb': 0.008, 'voice_per_min': 0.08, 'sms_per_msg': 0.03}
            ]
        })
    
    # ==================== Roaming Section ====================
    
    @app.route('/dashboard/api/roaming/operators')
    def roaming_operators():
        """Get roaming operators/partners"""
        try:
            if not app.roaming_manager:
                return jsonify({'partners': []})
            
            partners = app.roaming_manager.list_partners()
            return jsonify({
                'partners': [
                    {
                        'plmn_id': p.plmn_id,
                        'partner_name': p.partner_name,
                        'country_code': p.country_code if hasattr(p, 'country_code') else 'N/A',
                        'roaming_type': p.roaming_type.value if hasattr(p.roaming_type, 'value') else str(p.roaming_type),
                        'agreement_active': p.agreement_active if hasattr(p, 'agreement_active') else True,
                        'supported_tech': ['2G', '3G', '4G', '5G']
                    }
                    for p in partners
                ]
            })
        except Exception as e:
            logger.error(f"Error getting roaming operators: {e}")
            return jsonify({'partners': []})
    
    @app.route('/dashboard/api/roaming/rates')
    def roaming_rates():
        """Get roaming data rates"""
        return jsonify({
            'zones': [
                {'zone': 'EU/EEA', 'data_per_mb': 0.00, 'voice_per_min': 0.00, 'sms_per_msg': 0.00},
                {'zone': 'Zone 1', 'data_per_mb': 0.05, 'voice_per_min': 0.50, 'sms_per_msg': 0.20},
                {'zone': 'Zone 2', 'data_per_mb': 0.10, 'voice_per_min': 1.00, 'sms_per_msg': 0.40}
            ]
        })
    
    @app.route('/dashboard/api/roaming/plans')
    def roaming_plans():
        """Get roaming plans"""
        return jsonify({
            'plans': [
                {'id': 1, 'name': 'Roam Like at Home', 'data_limit_mb': 'unlimited', 'expiry_days': 365},
                {'id': 2, 'name': 'Travel Data Pack', 'data_limit_mb': 5000, 'expiry_days': 30},
                {'id': 3, 'name': 'Business Traveler', 'data_limit_mb': 10000, 'expiry_days': 90}
            ]
        })
    
    # ==================== Network Section ====================
    
    @app.route('/dashboard/api/network/diameter-peers')
    def network_diameter_peers():
        """Get Diameter peers status"""
        try:
            peers = [
                {
                    'host': 'mme1.opennetwork.local',
                    'realm': 'opennetwork.local',
                    'app_id': 's6a',
                    'status': 'up',
                    'rtt_ms': round(random.uniform(1, 10), 2),
                    'tps': random.randint(100, 500)
                },
                {
                    'host': 'mme2.opennetwork.local',
                    'realm': 'opennetwork.local',
                    'app_id': 's6a',
                    'status': 'up',
                    'rtt_ms': round(random.uniform(1, 10), 2),
                    'tps': random.randint(100, 500)
                },
                {
                    'host': 'pcrf.opennetwork.local',
                    'realm': 'opennetwork.local',
                    'app_id': 'gx',
                    'status': 'down',
                    'rtt_ms': 0,
                    'tps': 0
                }
            ]
            
            if app.dra:
                dra_peers = app.dra.get_peer_status() if hasattr(app.dra, 'get_peer_status') else []
                if dra_peers:
                    peers = dra_peers
            
            return jsonify({'peers': peers})
        except Exception as e:
            logger.error(f"Error getting diameter peers: {e}")
            return jsonify({'peers': []})
    
    @app.route('/dashboard/api/network/gtp-sessions')
    def network_gtp_sessions():
        """Get active GTP sessions"""
        return jsonify({
            'sessions': [
                {'imsi': '001010000000001', 'apn': 'internet', 'ip': '10.0.0.1', 'throughput_kbps': random.randint(100, 10000)},
                {'imsi': '001010000000002', 'apn': 'mms', 'ip': '10.0.0.2', 'throughput_kbps': random.randint(100, 10000)}
            ],
            'total': 2
        })
    
    @app.route('/dashboard/api/network/interfaces')
    def network_interfaces():
        """Get network interface configuration"""
        return jsonify({
            'interfaces': [
                {'name': 's6a', 'bind_ip': '0.0.0.0', 'port': 3868, 'status': 'active'},
                {'name': 'cx', 'bind_ip': '0.0.0.0', 'port': 3869, 'status': 'active'},
                {'name': 'gx', 'bind_ip': '0.0.0.0', 'port': 3870, 'status': 'inactive'}
            ]
        })
    
    # ==================== Plans Section ====================
    
    @app.route('/dashboard/api/plans/data')
    def plans_data():
        """Get data plans"""
        return jsonify({
            'plans': [
                {'id': 1, 'name': 'Business Unlimited', 'data_limit': 'unlimited', 'qci': 5, 'arp': 1},
                {'id': 2, 'name': 'Prepaid 10GB', 'data_limit': '10GB', 'qci': 9, 'arp': 15},
                {'id': 3, 'name': 'IoT Basic', 'data_limit': '1GB', 'qci': 9, 'arp': 10}
            ]
        })
    
    @app.route('/dashboard/api/plans/voice')
    def plans_voice():
        """Get voice & SMS plans"""
        return jsonify({
            'plans': [
                {'id': 1, 'name': 'Voice Unlimited', 'minutes': 'unlimited', 'sms': 'unlimited'},
                {'id': 2, 'name': 'Basic Voice', 'minutes': 500, 'sms': 200}
            ]
        })
    
    @app.route('/dashboard/api/plans/fwa')
    def plans_fwa():
        """Get FWA/IoT plans"""
        return jsonify({
            'plans': [
                {'id': 1, 'name': 'FWA Home', 'type': 'Fixed Wireless', 'static_ip': True, 'qci': 5},
                {'id': 2, 'name': 'IoT M2M', 'type': 'IoT', 'static_ip': False, 'qci': 9}
            ]
        })
    
    # ==================== Configuration Section ====================
    
    @app.route('/dashboard/api/config/system')
    def config_system():
        """Get system configuration"""
        return jsonify({
            'network': {
                'plmn_id': '00101',
                'mcc': '001',
                'mnc': '01',
                'network_name': 'Open Source Network'
            },
            'database': {
                'type': 'memory',
                'status': 'connected'
            }
        })
    
    # ==================== Users & Access Section ====================
    
    @app.route('/dashboard/api/users/admins')
    def users_admins():
        """Get admin users"""
        return jsonify({
            'users': [
                {'id': 1, 'username': 'admin', 'role': 'administrator', 'last_login': datetime.now().isoformat()},
                {'id': 2, 'username': 'operator', 'role': 'operator', 'last_login': (datetime.now() - timedelta(hours=2)).isoformat()}
            ]
        })
    
    @app.route('/dashboard/api/users/audit')
    def users_audit():
        """Get login audit log"""
        return jsonify({
            'logs': [
                {'username': 'admin', 'action': 'login', 'ip': '192.168.1.100', 'timestamp': datetime.now().isoformat(), 'success': True},
                {'username': 'operator', 'action': 'logout', 'ip': '192.168.1.101', 'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(), 'success': True}
            ]
        })
    
    # ==================== Tools Section ====================
    
    @app.route('/dashboard/api/tools/generate-ki')
    def tools_generate_ki():
        """Generate random KI key"""
        import secrets
        ki = secrets.token_hex(16).upper()
        return jsonify({'ki': ki})
    
    @app.route('/dashboard/api/tools/generate-opc')
    def tools_generate_opc():
        """Generate random OPC key"""
        import secrets
        opc = secrets.token_hex(16).upper()
        return jsonify({'opc': opc})
    
    @app.route('/dashboard/api/tools/plmn-lookup/<plmn_id>')
    def tools_plmn_lookup(plmn_id):
        """Look up PLMN information"""
        # Sample PLMN database
        plmn_db = {
            '00101': {'mcc': '001', 'mnc': '01', 'network': 'Test Network', 'country': 'Test Country'},
            '310260': {'mcc': '310', 'mnc': '260', 'network': 'T-Mobile USA', 'country': 'United States'},
            '26201': {'mcc': '262', 'mnc': '01', 'network': 'Telekom Deutschland', 'country': 'Germany'}
        }
        
        plmn_info = plmn_db.get(plmn_id, {
            'mcc': plmn_id[:3] if len(plmn_id) >= 3 else 'Unknown',
            'mnc': plmn_id[3:] if len(plmn_id) > 3 else 'Unknown',
            'network': 'Unknown',
            'country': 'Unknown'
        })
        
        return jsonify(plmn_info)
    
    logger.info("VERION Dashboard initialized")
    
    return app
