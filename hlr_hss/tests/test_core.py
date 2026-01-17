"""
Unit tests for HLR/HSS core functionality
"""
import pytest
from hlr_hss.core import HLR_HSS, Subscriber, LocationInfo, ENodeBProfile
from hlr_hss.database import MemoryDatabase


@pytest.fixture
def db():
    """Create test database"""
    return MemoryDatabase()


@pytest.fixture
def hlr_hss(db):
    """Create HLR/HSS instance"""
    return HLR_HSS(db)


@pytest.fixture
def sample_subscriber():
    """Create sample subscriber"""
    return Subscriber(
        imsi="001010000000001",
        msisdn="1234567890",
        ki="465B5CE8B199B49FAA5F0A2EE238A6BC",
        opc="E8ED289DEBA952E4283B54E88E6183CA",
        amf="8000",
        sqn=0,
    )


def test_create_subscriber(hlr_hss, sample_subscriber):
    """Test subscriber creation"""
    result = hlr_hss.create_subscriber(sample_subscriber)
    assert result is True
    
    retrieved = hlr_hss.get_subscriber(sample_subscriber.imsi)
    assert retrieved is not None
    assert retrieved.imsi == sample_subscriber.imsi
    assert retrieved.msisdn == sample_subscriber.msisdn


def test_get_nonexistent_subscriber(hlr_hss):
    """Test getting non-existent subscriber"""
    result = hlr_hss.get_subscriber("999999999999999")
    assert result is None


def test_update_subscriber(hlr_hss, sample_subscriber):
    """Test subscriber update"""
    hlr_hss.create_subscriber(sample_subscriber)
    
    updates = {'roaming_allowed': False}
    result = hlr_hss.update_subscriber(sample_subscriber.imsi, updates)
    assert result is True
    
    retrieved = hlr_hss.get_subscriber(sample_subscriber.imsi)
    assert retrieved.roaming_allowed is False


def test_delete_subscriber(hlr_hss, sample_subscriber):
    """Test subscriber deletion"""
    hlr_hss.create_subscriber(sample_subscriber)
    
    result = hlr_hss.delete_subscriber(sample_subscriber.imsi)
    assert result is True
    
    retrieved = hlr_hss.get_subscriber(sample_subscriber.imsi)
    assert retrieved is None


def test_update_location(hlr_hss, sample_subscriber):
    """Test location update"""
    hlr_hss.create_subscriber(sample_subscriber)
    
    location = LocationInfo(
        imsi=sample_subscriber.imsi,
        tracking_area="TAC001",
        serving_node="mme.opennetwork.local"
    )
    
    result = hlr_hss.update_location(location)
    assert result is True
    
    retrieved = hlr_hss.get_location(sample_subscriber.imsi)
    assert retrieved is not None
    assert retrieved.tracking_area == "TAC001"


def test_check_roaming_allowed(hlr_hss, sample_subscriber):
    """Test roaming check"""
    hlr_hss.create_subscriber(sample_subscriber)
    
    # Home network
    result = hlr_hss.check_roaming_allowed(sample_subscriber.imsi, "00101")
    assert result is True
    
    # Visited network
    result = hlr_hss.check_roaming_allowed(sample_subscriber.imsi, "00201")
    assert result is True


def test_is_subscriber_active(hlr_hss, sample_subscriber):
    """Test subscriber active check"""
    hlr_hss.create_subscriber(sample_subscriber)
    
    result = hlr_hss.is_subscriber_active(sample_subscriber.imsi)
    assert result is True
    
    # Deactivate subscriber
    hlr_hss.update_subscriber(sample_subscriber.imsi, {'subscriber_status': 'OPERATOR_DETERMINED_BARRING'})
    result = hlr_hss.is_subscriber_active(sample_subscriber.imsi)
    assert result is False


def test_get_subscriber_by_msisdn(hlr_hss, sample_subscriber):
    """Test getting subscriber by MSISDN"""
    hlr_hss.create_subscriber(sample_subscriber)
    
    retrieved = hlr_hss.get_subscriber_by_msisdn(sample_subscriber.msisdn)
    assert retrieved is not None
    assert retrieved.imsi == sample_subscriber.imsi


def test_register_enb_profile(hlr_hss):
    """Test eNodeB profile registration"""
    profile = ENodeBProfile(enb_id="srsenb-b210mini")
    result = hlr_hss.register_enb_profile(profile)
    assert result is True
    retrieved = hlr_hss.get_enb_profile("srsenb-b210mini")
    assert retrieved is not None
    assert retrieved.model == "LibreSDR B210mini"


def test_qos_normalization_clamps_ambr(hlr_hss):
    """Test QoS normalization clamps to AMBR"""
    subscriber = Subscriber(
        imsi="001010000000010",
        msisdn="1234567810",
        qos_profile={
            "mbr_uplink": 200000000,
            "mbr_downlink": 200000000,
            "gbr_uplink": 150000000,
            "gbr_downlink": 150000000,
        },
        ambr_uplink=100000000,
        ambr_downlink=120000000,
    )
    hlr_hss.create_subscriber(subscriber)
    retrieved = hlr_hss.get_subscriber(subscriber.imsi)
    assert retrieved.qos_profile["mbr_uplink"] == 100000000
    assert retrieved.qos_profile["mbr_downlink"] == 120000000
    assert retrieved.qos_profile["gbr_uplink"] == 100000000
    assert retrieved.qos_profile["gbr_downlink"] == 120000000
