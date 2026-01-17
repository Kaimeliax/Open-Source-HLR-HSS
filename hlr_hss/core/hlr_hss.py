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
                "preemption_vulnerability": False,
                "mbr_uplink": self.ambr_uplink,
                "mbr_downlink": self.ambr_downlink,
                "gbr_uplink": 0,
                "gbr_downlink": 0
            }
        else:
            self.qos_profile.setdefault("mbr_uplink", self.ambr_uplink)
            self.qos_profile.setdefault("mbr_downlink", self.ambr_downlink)
            self.qos_profile.setdefault("gbr_uplink", 0)
            self.qos_profile.setdefault("gbr_downlink", 0)
        if self.slice_info is None:
            self.slice_info = [
                {"sst": 1, "sd": "000001"}  # Default slice: eMBB
            ]


@dataclass
class ENodeBProfile:
    """eNodeB profile data structure"""
    enb_id: str
    model: Optional[str] = None
    downlink_modulation: Optional[str] = None
    uplink_modulation: Optional[str] = None
    mimo: Optional[str] = None
    max_transmission_mode: Optional[str] = None
    contiguous_bandwidth_mhz: Optional[int] = None
    carrier_bandwidth_options: Optional[List[str]] = None
    sample_rate_msps: Optional[float] = None
    duplex_modes: Optional[List[str]] = None
    qos_enforcement: bool = True
    cell_broadcast_supported: Optional[bool] = None

    def __post_init__(self):
        if self.model is None:
            self.model = "LibreSDR B210mini"
        if self.downlink_modulation is None:
            self.downlink_modulation = "1024QAM"
        if self.uplink_modulation is None:
            self.uplink_modulation = "256QAM"
        if self.mimo is None:
            self.mimo = "2x2"
        if self.max_transmission_mode is None:
            self.max_transmission_mode = "TM9"
        if self.contiguous_bandwidth_mhz is None:
            self.contiguous_bandwidth_mhz = 30
        if self.carrier_bandwidth_options is None:
            self.carrier_bandwidth_options = ["15+15", "20+10"]
        if self.sample_rate_msps is None:
            self.sample_rate_msps = 61.44
        if self.duplex_modes is None:
            self.duplex_modes = ["TDD", "FDD"]
        if self.cell_broadcast_supported is None:
            self.cell_broadcast_supported = False


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
        self.enb_profiles: Dict[str, ENodeBProfile] = {}
        self.logger.info("HLR/HSS initialized")

    def _clamp_qos_value(self, value: Any, limit: int) -> int:
        try:
            value_int = int(value)
        except (TypeError, ValueError):
            self.logger.warning(f"Invalid QoS value {value}; defaulting to {limit}")
            value_int = limit
        return min(value_int, limit)

    def _normalize_qos_profile(self, qos_profile: Optional[Dict[str, Any]], ambr_uplink: int, ambr_downlink: int) -> Dict[str, Any]:
        normalized = dict(qos_profile or {})
        normalized.setdefault("mbr_uplink", ambr_uplink)
        normalized.setdefault("mbr_downlink", ambr_downlink)
        normalized.setdefault("gbr_uplink", 0)
        normalized.setdefault("gbr_downlink", 0)
        normalized["mbr_uplink"] = self._clamp_qos_value(normalized.get("mbr_uplink"), ambr_uplink)
        normalized["mbr_downlink"] = self._clamp_qos_value(normalized.get("mbr_downlink"), ambr_downlink)
        normalized["gbr_uplink"] = self._clamp_qos_value(normalized.get("gbr_uplink"), ambr_uplink)
        normalized["gbr_downlink"] = self._clamp_qos_value(normalized.get("gbr_downlink"), ambr_downlink)
        return normalized

    def register_enb_profile(self, profile: ENodeBProfile) -> bool:
        if profile.enb_id in self.enb_profiles:
            return False
        self.enb_profiles[profile.enb_id] = profile
        return True

    def get_enb_profile(self, enb_id: str) -> Optional[ENodeBProfile]:
        return self.enb_profiles.get(enb_id)

    def update_enb_profile(self, enb_id: str, updates: Dict[str, Any]) -> Optional[bool]:
        profile = self.enb_profiles.get(enb_id)
        if not profile:
            return None
        if "enb_id" in updates and updates["enb_id"] != enb_id:
            self.logger.warning(f"eNodeB profile ID mismatch for {enb_id}")
            return False
        profile_data = profile.__dict__.copy()
        profile_data.update(updates)
        profile_data["enb_id"] = enb_id
        try:
            self.enb_profiles[enb_id] = ENodeBProfile(**profile_data)
            return True
        except (TypeError, ValueError) as e:
            self.logger.warning(f"Failed to update eNodeB profile {enb_id}: {e}")
            return False

    def delete_enb_profile(self, enb_id: str) -> bool:
        if enb_id not in self.enb_profiles:
            return False
        del self.enb_profiles[enb_id]
        return True

    def list_enb_profiles(self) -> List[ENodeBProfile]:
        return list(self.enb_profiles.values())
    
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
            subscriber.qos_profile = self._normalize_qos_profile(
                subscriber.qos_profile,
                subscriber.ambr_uplink,
                subscriber.ambr_downlink
            )
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
            if any(key in updates for key in ("qos_profile", "ambr_uplink", "ambr_downlink")):
                subscriber = self.get_subscriber(imsi)
                if not subscriber:
                    return False
                ambr_uplink = updates.get("ambr_uplink", subscriber.ambr_uplink)
                ambr_downlink = updates.get("ambr_downlink", subscriber.ambr_downlink)
                qos_profile = updates.get("qos_profile", subscriber.qos_profile)
                updates["qos_profile"] = self._normalize_qos_profile(qos_profile, ambr_uplink, ambr_downlink)
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
