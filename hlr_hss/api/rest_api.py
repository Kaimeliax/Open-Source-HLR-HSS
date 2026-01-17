"""
REST API for HLR/HSS management
Provides HTTP interface for subscriber management, monitoring, and configuration
"""
import logging
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
from typing import Optional

from hlr_hss.core import Subscriber, ENodeBProfile

logger = logging.getLogger(__name__)


def create_api(hlr_hss, ocs=None, roaming_manager=None, dra=None):
    """
    Create Flask API application
    
    Args:
        hlr_hss: HLR_HSS instance
        ocs: OnlineChargingSystem instance (optional)
        roaming_manager: RoamingManager instance (optional)
        dra: DiameterRoutingAgent instance (optional)
        
    Returns:
        Flask application
    """
    app = Flask(__name__)
    CORS(app)
    api = Api(app)
    
    # Store instances
    app.hlr_hss = hlr_hss
    app.ocs = ocs
    app.roaming_manager = roaming_manager
    app.dra = dra
    
    class HealthCheck(Resource):
        def get(self):
            """Health check endpoint"""
            return {'status': 'healthy', 'service': 'HLR/HSS'}, 200
    
    class SubscriberResource(Resource):
        def get(self, imsi):
            """Get subscriber by IMSI"""
            subscriber = app.hlr_hss.get_subscriber(imsi)
            if not subscriber:
                return {'error': 'Subscriber not found'}, 404
            
            return {
                'imsi': subscriber.imsi,
                'msisdn': subscriber.msisdn,
                'subscriber_status': subscriber.subscriber_status,
                'roaming_allowed': subscriber.roaming_allowed,
                'apn_list': subscriber.apn_list,
                'serving_mme': subscriber.serving_mme,
                'qos_profile': subscriber.qos_profile,
                'ambr_uplink': subscriber.ambr_uplink,
                'ambr_downlink': subscriber.ambr_downlink,
            }, 200
        
        def post(self, imsi):
            """Create new subscriber"""
            data = request.json
            
            subscriber = Subscriber(
                imsi=imsi,
                msisdn=data.get('msisdn'),
                ki=data.get('ki'),
                opc=data.get('opc'),
                amf=data.get('amf', '8000'),
                sqn=data.get('sqn', 0),
                subscriber_status=data.get('subscriber_status', 'SERVICE_GRANTED'),
                roaming_allowed=data.get('roaming_allowed', True),
                qos_profile=data.get('qos_profile'),
                ambr_uplink=data.get('ambr_uplink', 100000000),
                ambr_downlink=data.get('ambr_downlink', 100000000),
            )
            
            success = app.hlr_hss.create_subscriber(subscriber)
            
            if success:
                return {'message': 'Subscriber created'}, 201
            else:
                return {'error': 'Failed to create subscriber'}, 500
        
        def put(self, imsi):
            """Update subscriber"""
            data = request.json
            
            success = app.hlr_hss.update_subscriber(imsi, data)
            
            if success:
                return {'message': 'Subscriber updated'}, 200
            else:
                return {'error': 'Failed to update subscriber'}, 500
        
        def delete(self, imsi):
            """Delete subscriber"""
            success = app.hlr_hss.delete_subscriber(imsi)
            
            if success:
                return {'message': 'Subscriber deleted'}, 200
            else:
                return {'error': 'Failed to delete subscriber'}, 500
    
    class SubscriberList(Resource):
        def get(self):
            """List subscribers"""
            # This would need pagination in production
            if hasattr(app.hlr_hss.db, 'list_subscribers'):
                subscribers = app.hlr_hss.db.list_subscribers(limit=100)
                return {'subscribers': subscribers, 'count': len(subscribers)}, 200
            else:
                return {'error': 'List not supported'}, 501

    class EnbProfileList(Resource):
        def get(self):
            """List eNodeB profiles"""
            profiles = app.hlr_hss.list_enb_profiles()
            return {
                'enb_profiles': [profile.__dict__ for profile in profiles],
                'count': len(profiles)
            }, 200

        def post(self):
            """Create eNodeB profile"""
            data = request.json or {}
            enb_id = data.get('enb_id')
            if not enb_id:
                return {'error': 'enb_id is required'}, 400

            try:
                profile = ENodeBProfile(**data)
            except (TypeError, ValueError) as e:
                logger.warning(f"Invalid eNodeB profile payload: {e}")
                return {'error': 'Invalid eNodeB profile payload'}, 400
            success = app.hlr_hss.register_enb_profile(profile)

            if success:
                return {'message': 'eNodeB profile created'}, 201
            else:
                return {'error': 'eNodeB profile already exists'}, 409

    class EnbProfileResource(Resource):
        def get(self, enb_id):
            """Get eNodeB profile"""
            profile = app.hlr_hss.get_enb_profile(enb_id)
            if not profile:
                return {'error': 'eNodeB profile not found'}, 404
            return profile.__dict__, 200

        def put(self, enb_id):
            """Update eNodeB profile"""
            data = request.json or {}
            result = app.hlr_hss.update_enb_profile(enb_id, data)
            if result is None:
                return {'error': 'eNodeB profile not found'}, 404
            if result:
                return {'message': 'eNodeB profile updated'}, 200
            else:
                return {'error': 'Invalid eNodeB profile update'}, 400

        def delete(self, enb_id):
            """Delete eNodeB profile"""
            success = app.hlr_hss.delete_enb_profile(enb_id)
            if success:
                return {'message': 'eNodeB profile deleted'}, 200
            else:
                return {'error': 'Failed to delete eNodeB profile'}, 404
    
    class LocationResource(Resource):
        def get(self, imsi):
            """Get subscriber location"""
            location = app.hlr_hss.get_location(imsi)
            if not location:
                return {'error': 'Location not found'}, 404
            
            return {
                'imsi': location.imsi,
                'serving_node': location.serving_node,
                'tracking_area': location.tracking_area,
                'last_update': str(location.last_update) if location.last_update else None,
            }, 200
    
    class AuthVectorResource(Resource):
        def post(self, imsi):
            """Generate authentication vector"""
            subscriber = app.hlr_hss.get_subscriber(imsi)
            if not subscriber:
                return {'error': 'Subscriber not found'}, 404
            
            from hlr_hss.authentication import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            auth_vector = auth_manager.generate_auth_vector(
                'milenage',
                subscriber.ki,
                subscriber.opc,
                subscriber.amf,
                subscriber.sqn
            )
            
            if auth_vector:
                # Update SQN
                app.hlr_hss.update_subscriber(imsi, {'sqn': subscriber.sqn + 1})
                return auth_vector, 200
            else:
                return {'error': 'Failed to generate auth vector'}, 500
    
    class OCSSessionResource(Resource):
        def get(self, session_id=None):
            """Get OCS session(s)"""
            if not app.ocs:
                return {'error': 'OCS not available'}, 501
            
            if session_id:
                session = app.ocs.get_session(session_id)
                if not session:
                    return {'error': 'Session not found'}, 404
                
                return {
                    'session_id': session.session_id,
                    'imsi': session.imsi,
                    'current_balance': session.current_balance,
                    'data_usage_bytes': session.data_usage_bytes,
                }, 200
            else:
                sessions = app.ocs.list_active_sessions()
                return {
                    'sessions': [
                        {
                            'session_id': s.session_id,
                            'imsi': s.imsi,
                            'current_balance': s.current_balance,
                        }
                        for s in sessions
                    ],
                    'count': len(sessions)
                }, 200
    
    class RoamingPartnerResource(Resource):
        def get(self, plmn_id=None):
            """Get roaming partner(s)"""
            if not app.roaming_manager:
                return {'error': 'Roaming manager not available'}, 501
            
            if plmn_id:
                partner = app.roaming_manager.get_partner(plmn_id)
                if not partner:
                    return {'error': 'Partner not found'}, 404
                
                return {
                    'plmn_id': partner.plmn_id,
                    'partner_name': partner.partner_name,
                    'country_code': partner.country_code,
                    'roaming_type': partner.roaming_type.value,
                    'agreement_active': partner.agreement_active,
                }, 200
            else:
                partners = app.roaming_manager.list_partners()
                return {
                    'partners': [
                        {
                            'plmn_id': p.plmn_id,
                            'partner_name': p.partner_name,
                            'roaming_type': p.roaming_type.value,
                        }
                        for p in partners
                    ],
                    'count': len(partners)
                }, 200
    
    class DRAStatusResource(Resource):
        def get(self):
            """Get DRA status"""
            if not app.dra:
                return {'error': 'DRA not available'}, 501
            
            return {
                'host': app.dra.host,
                'realm': app.dra.realm,
                'peers': app.dra.get_peer_status(),
                'routing_rules': app.dra.get_routing_rules(),
            }, 200
    
    # Register endpoints
    api.add_resource(HealthCheck, '/health')
    api.add_resource(SubscriberResource, '/api/v1/subscribers/<string:imsi>')
    api.add_resource(SubscriberList, '/api/v1/subscribers')
    api.add_resource(EnbProfileList, '/api/v1/enb')
    api.add_resource(EnbProfileResource, '/api/v1/enb/<string:enb_id>')
    api.add_resource(LocationResource, '/api/v1/location/<string:imsi>')
    api.add_resource(AuthVectorResource, '/api/v1/auth/<string:imsi>')
    api.add_resource(OCSSessionResource, '/api/v1/ocs/sessions', '/api/v1/ocs/sessions/<string:session_id>')
    api.add_resource(RoamingPartnerResource, '/api/v1/roaming/partners', '/api/v1/roaming/partners/<string:plmn_id>')
    api.add_resource(DRAStatusResource, '/api/v1/dra/status')
    
    logger.info("API initialized")
    
    return app
