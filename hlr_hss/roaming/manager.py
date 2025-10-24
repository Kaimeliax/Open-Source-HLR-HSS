"""
Roaming support and management
Handles roaming agreements, partner networks, and roaming policies
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RoamingType(Enum):
    """Types of roaming"""
    NATIONAL = "national"
    INTERNATIONAL = "international"
    LOCAL = "local"


@dataclass
class RoamingPartner:
    """Roaming partner network configuration"""
    partner_id: str
    partner_name: str
    plmn_id: str  # MCC+MNC
    country_code: str
    
    # Agreement details
    roaming_type: RoamingType
    agreement_active: bool = True
    
    # Financial
    data_rate: float = 0.0  # Per MB
    voice_rate: float = 0.0  # Per minute
    sms_rate: float = 0.0  # Per SMS
    
    # Technical
    s6a_peers: List[str] = None
    diameter_realm: Optional[str] = None
    
    # Restrictions
    max_data_speed_mbps: Optional[int] = None
    allowed_services: List[str] = None
    
    def __post_init__(self):
        if self.s6a_peers is None:
            self.s6a_peers = []
        if self.allowed_services is None:
            self.allowed_services = ["voice", "sms", "data"]


@dataclass
class RoamingPolicy:
    """Roaming policy for subscriber groups"""
    policy_id: str
    name: str
    
    # Allowed roaming types
    national_roaming: bool = True
    international_roaming: bool = False
    
    # Allowed partner PLMNs (empty = all partners allowed)
    allowed_plmns: List[str] = None
    blocked_plmns: List[str] = None
    
    # Service restrictions while roaming
    data_roaming: bool = True
    voice_roaming: bool = True
    sms_roaming: bool = True
    
    # Data limits
    daily_data_limit_mb: Optional[int] = None
    monthly_data_limit_mb: Optional[int] = None
    
    # Cost controls
    max_daily_cost: Optional[float] = None
    max_monthly_cost: Optional[float] = None
    
    def __post_init__(self):
        if self.allowed_plmns is None:
            self.allowed_plmns = []
        if self.blocked_plmns is None:
            self.blocked_plmns = []


class RoamingManager:
    """
    Manages roaming agreements and policies
    """
    
    def __init__(self, home_plmn: str):
        """
        Initialize roaming manager
        
        Args:
            home_plmn: Home network PLMN ID (MCC+MNC)
        """
        self.home_plmn = home_plmn
        self.partners: Dict[str, RoamingPartner] = {}
        self.policies: Dict[str, RoamingPolicy] = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Roaming Manager initialized for PLMN {home_plmn}")
    
    def add_partner(self, partner: RoamingPartner):
        """
        Add roaming partner
        
        Args:
            partner: Roaming partner configuration
        """
        self.partners[partner.plmn_id] = partner
        self.logger.info(f"Added roaming partner: {partner.partner_name} ({partner.plmn_id})")
    
    def remove_partner(self, plmn_id: str):
        """
        Remove roaming partner
        
        Args:
            plmn_id: Partner PLMN ID
        """
        if plmn_id in self.partners:
            partner_name = self.partners[plmn_id].partner_name
            del self.partners[plmn_id]
            self.logger.info(f"Removed roaming partner: {partner_name}")
    
    def get_partner(self, plmn_id: str) -> Optional[RoamingPartner]:
        """
        Get roaming partner by PLMN ID
        
        Args:
            plmn_id: Partner PLMN ID
            
        Returns:
            RoamingPartner or None
        """
        return self.partners.get(plmn_id)
    
    def add_policy(self, policy: RoamingPolicy):
        """
        Add roaming policy
        
        Args:
            policy: Roaming policy
        """
        self.policies[policy.policy_id] = policy
        self.logger.info(f"Added roaming policy: {policy.name}")
    
    def remove_policy(self, policy_id: str):
        """
        Remove roaming policy
        
        Args:
            policy_id: Policy ID
        """
        if policy_id in self.policies:
            del self.policies[policy_id]
            self.logger.info(f"Removed roaming policy: {policy_id}")
    
    def get_policy(self, policy_id: str) -> Optional[RoamingPolicy]:
        """
        Get roaming policy by ID
        
        Args:
            policy_id: Policy ID
            
        Returns:
            RoamingPolicy or None
        """
        return self.policies.get(policy_id)
    
    def check_roaming_allowed(self, subscriber_imsi: str, visited_plmn: str,
                             policy_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if roaming is allowed
        
        Args:
            subscriber_imsi: Subscriber IMSI
            visited_plmn: Visited PLMN ID
            policy_id: Optional roaming policy ID
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check if in home network
        home_plmn = subscriber_imsi[:5]  # First 5 digits: MCC+MNC
        if home_plmn == visited_plmn:
            return True, "Home network"
        
        # Check if partner exists and agreement is active
        partner = self.partners.get(visited_plmn)
        if not partner:
            return False, "No roaming agreement with visited network"
        
        if not partner.agreement_active:
            return False, "Roaming agreement is not active"
        
        # Check policy if provided
        if policy_id:
            policy = self.policies.get(policy_id)
            if not policy:
                return False, "Invalid roaming policy"
            
            # Check roaming type
            if partner.roaming_type == RoamingType.NATIONAL and not policy.national_roaming:
                return False, "National roaming not allowed by policy"
            
            if partner.roaming_type == RoamingType.INTERNATIONAL and not policy.international_roaming:
                return False, "International roaming not allowed by policy"
            
            # Check PLMN whitelist/blacklist
            if policy.allowed_plmns and visited_plmn not in policy.allowed_plmns:
                return False, "Visited PLMN not in allowed list"
            
            if visited_plmn in policy.blocked_plmns:
                return False, "Visited PLMN is blocked"
        
        return True, "Roaming allowed"
    
    def get_roaming_rates(self, visited_plmn: str) -> Optional[Dict[str, float]]:
        """
        Get roaming rates for visited PLMN
        
        Args:
            visited_plmn: Visited PLMN ID
            
        Returns:
            Dictionary of rates or None
        """
        partner = self.partners.get(visited_plmn)
        if not partner:
            return None
        
        return {
            'data_rate': partner.data_rate,
            'voice_rate': partner.voice_rate,
            'sms_rate': partner.sms_rate,
        }
    
    def list_partners(self, roaming_type: Optional[RoamingType] = None) -> List[RoamingPartner]:
        """
        List roaming partners
        
        Args:
            roaming_type: Optional filter by roaming type
            
        Returns:
            List of roaming partners
        """
        partners = list(self.partners.values())
        
        if roaming_type:
            partners = [p for p in partners if p.roaming_type == roaming_type]
        
        return partners
    
    def list_policies(self) -> List[RoamingPolicy]:
        """
        List all roaming policies
        
        Returns:
            List of roaming policies
        """
        return list(self.policies.values())
    
    def get_partner_diameter_realm(self, plmn_id: str) -> Optional[str]:
        """
        Get Diameter realm for partner PLMN
        
        Args:
            plmn_id: Partner PLMN ID
            
        Returns:
            Diameter realm or None
        """
        partner = self.partners.get(plmn_id)
        if partner:
            return partner.diameter_realm
        return None
