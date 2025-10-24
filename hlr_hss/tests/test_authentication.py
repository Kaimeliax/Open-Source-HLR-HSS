"""
Unit tests for authentication algorithms
"""
import pytest
from hlr_hss.authentication import Milenage, XOR, AuthenticationManager


def test_milenage_auth_vector():
    """Test Milenage authentication vector generation"""
    milenage = Milenage()
    
    k = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    opc = "E8ED289DEBA952E4283B54E88E6183CA"
    amf = "8000"
    sqn = 0
    
    auth_vec = milenage.generate_auth_vector(k, opc, amf, sqn)
    
    assert auth_vec is not None
    assert 'rand' in auth_vec
    assert 'autn' in auth_vec
    assert 'xres' in auth_vec
    assert 'kasme' in auth_vec
    assert 'ck' in auth_vec
    assert 'ik' in auth_vec
    
    # Check lengths
    assert len(auth_vec['rand']) == 32  # 16 bytes hex
    assert len(auth_vec['xres']) == 16  # 8 bytes hex
    assert len(auth_vec['kasme']) == 64  # 32 bytes hex


def test_xor_auth_vector():
    """Test XOR authentication vector generation"""
    xor = XOR()
    
    k = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    sqn = 0
    
    auth_vec = xor.generate_auth_vector(k, sqn)
    
    assert auth_vec is not None
    assert 'rand' in auth_vec
    assert 'autn' in auth_vec
    assert 'xres' in auth_vec
    assert 'kasme' in auth_vec


def test_auth_manager_milenage():
    """Test authentication manager with Milenage"""
    auth_mgr = AuthenticationManager()
    
    k = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    opc = "E8ED289DEBA952E4283B54E88E6183CA"
    amf = "8000"
    sqn = 0
    
    auth_vec = auth_mgr.generate_auth_vector('milenage', k, opc, amf, sqn)
    
    assert auth_vec is not None
    assert 'rand' in auth_vec


def test_auth_manager_xor():
    """Test authentication manager with XOR"""
    auth_mgr = AuthenticationManager()
    
    k = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    amf = "8000"
    sqn = 0
    
    auth_vec = auth_mgr.generate_auth_vector('xor', k, None, amf, sqn)
    
    assert auth_vec is not None
    assert 'rand' in auth_vec


def test_verify_response():
    """Test response verification"""
    auth_mgr = AuthenticationManager()
    
    xres = "1234567890abcdef"
    res = "1234567890abcdef"
    
    result = auth_mgr.verify_response(xres, res)
    assert result is True
    
    result = auth_mgr.verify_response(xres, "0000000000000000")
    assert result is False
