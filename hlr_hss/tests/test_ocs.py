"""
Unit tests for OCS (Online Charging System)
"""
import pytest
from hlr_hss.ocs import OnlineChargingSystem, ChargingType, RequestType
from hlr_hss.database import MemoryDatabase


@pytest.fixture
def db():
    """Create test database"""
    return MemoryDatabase()


@pytest.fixture
def ocs(db):
    """Create OCS instance"""
    return OnlineChargingSystem(db)


def test_initial_request(ocs):
    """Test initial CCR"""
    request = {
        'cc_request_type': RequestType.INITIAL_REQUEST,
        'session_id': 'session_001',
        'subscription_id': {
            'imsi': '001010000000001',
            'msisdn': '1234567890'
        },
        'service_identifier': 'data',
        'requested_service_unit': {
            'total_octets': 100 * 1024 * 1024  # 100MB
        }
    }
    
    response = ocs.handle_credit_control_request(request)
    
    assert response['result_code'] == 2001  # SUCCESS
    assert 'granted_service_unit' in response
    assert 'total_octets' in response['granted_service_unit']


def test_update_request(ocs):
    """Test update CCR"""
    # First, initial request
    initial_request = {
        'cc_request_type': RequestType.INITIAL_REQUEST,
        'session_id': 'session_002',
        'subscription_id': {
            'imsi': '001010000000002',
            'msisdn': '1234567891'
        },
        'service_identifier': 'data',
        'requested_service_unit': {
            'total_octets': 50 * 1024 * 1024
        }
    }
    
    initial_response = ocs.handle_credit_control_request(initial_request)
    assert initial_response['result_code'] == 2001
    
    # Then, update request
    update_request = {
        'cc_request_type': RequestType.UPDATE_REQUEST,
        'session_id': 'session_002',
        'used_service_unit': {
            'total_octets': 10 * 1024 * 1024  # 10MB used
        },
        'requested_service_unit': {
            'total_octets': 50 * 1024 * 1024
        }
    }
    
    update_response = ocs.handle_credit_control_request(update_request)
    assert update_response['result_code'] == 2001


def test_termination_request(ocs):
    """Test termination CCR"""
    # Initial request
    initial_request = {
        'cc_request_type': RequestType.INITIAL_REQUEST,
        'session_id': 'session_003',
        'subscription_id': {
            'imsi': '001010000000003',
            'msisdn': '1234567892'
        },
        'service_identifier': 'data',
        'requested_service_unit': {
            'total_octets': 50 * 1024 * 1024
        }
    }
    
    ocs.handle_credit_control_request(initial_request)
    
    # Termination request
    term_request = {
        'cc_request_type': RequestType.TERMINATION_REQUEST,
        'session_id': 'session_003',
        'used_service_unit': {
            'total_octets': 20 * 1024 * 1024  # 20MB used
        }
    }
    
    term_response = ocs.handle_credit_control_request(term_request)
    assert term_response['result_code'] == 2001
    
    # Session should be removed
    session = ocs.get_session('session_003')
    assert session is None


def test_event_request_sms(ocs):
    """Test event CCR for SMS"""
    request = {
        'cc_request_type': RequestType.EVENT_REQUEST,
        'session_id': 'event_001',
        'subscription_id': {
            'imsi': '001010000000004',
            'msisdn': '1234567893'
        },
        'service_identifier': 'sms',
        'requested_service_unit': {
            'service_specific_units': 1
        }
    }
    
    response = ocs.handle_credit_control_request(request)
    assert response['result_code'] == 2001
