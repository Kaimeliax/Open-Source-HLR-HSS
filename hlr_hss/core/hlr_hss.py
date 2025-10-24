"""
Core HLR/HSS functionality
Manages subscriber data, authentication, and location information
"""
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Subscriber:
    """Subscriber profile data structure"""
    imsi: str
    msisdn: str
    imei: Optional[str] = None
    
    # Authentication credentials
    ki: Optional[str] = None  # K for Milenage
    opc: Optional[str] = None  # OPc for Milenage
    op: Optional[str] = None  # OP for Milenage
    amf: str = "8000"  # Authentication Management Field
    sqn: int = 0  # Sequence Number
    
    # Network parameters
    apn_list: List[str] = None
    default_apn: Optional[str] = None
    subscribed_rau_tau_timer: int = 3600
    
    # Status
    subscriber_status: str = "SERVICE_GRANTED"  # SERVICE_GRANTED, OPERATOR_DETERMINED_BARRING
    network_access_mode: str = "PACKET_AND_CIRCUIT"  # PACKET_AND_CIRCUIT, ONLY_PACKET
    roaming_allowed: bool = True
    
    # Location information
    serving_mme: Optional[str] = None
    serving_msc: Optional[str] = None
    serving_sgsn: Optional[str] = None
    vlr_number: Optional[str] = None
    mme_host: Optional[str] = None
    mme_realm: Optional[str] = None
    
    # 5G specific
    serving_amf: Optional[str] = None
    slice_info: Optional[List[Dict]] = None  # Network slicing info
    
    # QoS Profile
    qos_profile: Optional[Dict] = None
    ambr_uplink: int = 100000000  # bits/s
    ambr_downlink: int = 100000000  # bits/s
    
    # Charging
    charging_characteristics: Optional[str] = None
    ocs_enabled: bool = True
    
    def __post_init__(self):
        if self.apn_list is None:
            self.apn_list = ["internet"]
        if self.default_apn is None:
            self.default_apn = "internet"
        if self.qos_profile is None:
            self.qos_profile = {
                "qci": 9,
                "priority": 8,
                "preemption_capability": True,
                "preemption_vulnerability": False
            }
        if self.slice_info is None:
            self.slice_info = [
                {"sst": 1, "sd": "000001"}  # Default slice: eMBB
            ]


@dataclass
class LocationInfo:
    """Subscriber location and tracking information"""
    imsi: str
    location_area: Optional[str] = None
    routing_area: Optional[str] = None
    tracking_area: Optional[str] = None
    cell_id: Optional[str] = None
    serving_node: Optional[str] = None
    last_update: Optional[datetime] = None


class HLR_HSS:
    """
    Main HLR/HSS class
    Handles subscriber management, authentication, and network functions
    """
    
    def __init__(self, db_handler):
        """
        Initialize HLR/HSS
        
        Args:
            db_handler: Database handler instance
        """
        self.db = db_handler
        self.logger = logging.getLogger(__name__)
        self.logger.info("HLR/HSS initialized")
    
    def get_subscriber(self, imsi: str) -> Optional[Subscriber]:
        """
        Retrieve subscriber data by IMSI
        
        Args:
            imsi: International Mobile Subscriber Identity
            
        Returns:
            Subscriber object or None if not found
        """
        try:
            sub_data = self.db.get_subscriber(imsi)
            if sub_data:
                return Subscriber(**sub_data)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving subscriber {imsi}: {e}")
            return None
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Subscriber]:
        """
        Retrieve subscriber data by MSISDN (phone number)
        
        Args:
            msisdn: Mobile Station ISDN Number
            
        Returns:
            Subscriber object or None if not found
        """
        try:
            sub_data = self.db.get_subscriber_by_msisdn(msisdn)
            if sub_data:
                return Subscriber(**sub_data)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving subscriber by MSISDN {msisdn}: {e}")
            return None
    
    def create_subscriber(self, subscriber: Subscriber) -> bool:
        """
        Create new subscriber entry
        
        Args:
            subscriber: Subscriber object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            sub_dict = subscriber.__dict__
            return self.db.create_subscriber(sub_dict)
        except Exception as e:
            self.logger.error(f"Error creating subscriber {subscriber.imsi}: {e}")
            return False
    
    def update_subscriber(self, imsi: str, updates: Dict[str, Any]) -> bool:
        """
        Update subscriber data
        
        Args:
            imsi: International Mobile Subscriber Identity
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.update_subscriber(imsi, updates)
        except Exception as e:
            self.logger.error(f"Error updating subscriber {imsi}: {e}")
            return False
    
    def delete_subscriber(self, imsi: str) -> bool:
        """
        Delete subscriber entry
        
        Args:
            imsi: International Mobile Subscriber Identity
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.db.delete_subscriber(imsi)
        except Exception as e:
            self.logger.error(f"Error deleting subscriber {imsi}: {e}")
            return False
    
    def update_location(self, location_info: LocationInfo) -> bool:
        """
        Update subscriber location information
        
        Args:
            location_info: LocationInfo object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            location_dict = location_info.__dict__
            location_dict['last_update'] = datetime.now()
            return self.db.update_location(location_info.imsi, location_dict)
        except Exception as e:
            self.logger.error(f"Error updating location for {location_info.imsi}: {e}")
            return False
    
    def get_location(self, imsi: str) -> Optional[LocationInfo]:
        """
        Get subscriber location information
        
        Args:
            imsi: International Mobile Subscriber Identity
            
        Returns:
            LocationInfo object or None if not found
        """
        try:
            loc_data = self.db.get_location(imsi)
            if loc_data:
                return LocationInfo(**loc_data)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving location for {imsi}: {e}")
            return None
    
    def check_roaming_allowed(self, imsi: str, visited_plmn: str) -> bool:
        """
        Check if roaming is allowed for subscriber in visited PLMN
        
        Args:
            imsi: International Mobile Subscriber Identity
            visited_plmn: Visited PLMN ID
            
        Returns:
            True if roaming allowed, False otherwise
        """
        subscriber = self.get_subscriber(imsi)
        if not subscriber:
            return False
        
        if not subscriber.roaming_allowed:
            return False
        
        # Check roaming agreements (could be extended with PLMN whitelist/blacklist)
        home_plmn = imsi[:5]  # First 5 digits: MCC+MNC
        
        # For now, allow all roaming if subscriber has roaming enabled
        return True
    
    def is_subscriber_active(self, imsi: str) -> bool:
        """
        Check if subscriber is active and authorized
        
        Args:
            imsi: International Mobile Subscriber Identity
            
        Returns:
            True if active, False otherwise
        """
        subscriber = self.get_subscriber(imsi)
        if not subscriber:
            return False
        
        return subscriber.subscriber_status == "SERVICE_GRANTED"
