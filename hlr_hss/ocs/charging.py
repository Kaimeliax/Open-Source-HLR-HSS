"""
Online Charging System (OCS) implementation
Implements Gy/Ro interface for online charging
3GPP TS 32.299
"""
import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import IntEnum
from datetime import datetime

logger = logging.getLogger(__name__)


class ChargingType(IntEnum):
    """Charging types"""
    PREPAID = 0
    POSTPAID = 1
    FLAT_RATE = 2


class RequestType(IntEnum):
    """Credit Control Request Types"""
    INITIAL_REQUEST = 1
    UPDATE_REQUEST = 2
    TERMINATION_REQUEST = 3
    EVENT_REQUEST = 4


class ResultCode(IntEnum):
    """Result codes for charging"""
    SUCCESS = 2001
    END_USER_SERVICE_DENIED = 4010
    CREDIT_LIMIT_REACHED = 4012
    USER_UNKNOWN = 5030
    RATING_FAILED = 5031


@dataclass
class ChargingSession:
    """Charging session data"""
    session_id: str
    imsi: str
    msisdn: str
    charging_type: ChargingType
    
    # Balance tracking
    initial_balance: float = 0.0
    current_balance: float = 0.0
    reserved_balance: float = 0.0
    
    # Usage tracking
    data_usage_bytes: int = 0
    voice_usage_seconds: int = 0
    sms_usage_count: int = 0
    
    # Session info
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    apn: Optional[str] = None
    
    # Granted units
    granted_data_bytes: int = 0
    granted_voice_seconds: int = 0
    granted_sms_count: int = 0
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.last_update is None:
            self.last_update = datetime.now()


@dataclass
class RatingRule:
    """Rating rule for charging calculation"""
    name: str
    service_type: str  # 'data', 'voice', 'sms'
    
    # Pricing
    cost_per_unit: float  # Cost per MB, per minute, per SMS
    
    # Conditions
    time_of_day_start: Optional[str] = None
    time_of_day_end: Optional[str] = None
    roaming: Optional[bool] = None
    
    # Quotas
    quota_threshold: Optional[float] = None


class OnlineChargingSystem:
    """
    Online Charging System (OCS)
    Handles real-time charging and credit control
    """
    
    def __init__(self, db_handler):
        """
        Initialize OCS
        
        Args:
            db_handler: Database handler for persistence
        """
        self.db = db_handler
        self.sessions = {}  # In-memory session cache
        self.rating_rules = self._initialize_rating_rules()
        self.logger = logging.getLogger(__name__)
        self.logger.info("OCS initialized")
    
    def _initialize_rating_rules(self) -> List[RatingRule]:
        """Initialize default rating rules"""
        return [
            RatingRule(
                name="data_standard",
                service_type="data",
                cost_per_unit=0.01,  # $0.01 per MB
            ),
            RatingRule(
                name="voice_standard",
                service_type="voice",
                cost_per_unit=0.10,  # $0.10 per minute
            ),
            RatingRule(
                name="sms_standard",
                service_type="sms",
                cost_per_unit=0.05,  # $0.05 per SMS
            ),
        ]
    
    def handle_credit_control_request(self, request: Dict) -> Dict:
        """
        Handle Credit-Control-Request (CCR)
        
        Args:
            request: CCR message dictionary
            
        Returns:
            Credit-Control-Answer (CCA) dictionary
        """
        request_type = request.get('cc_request_type', RequestType.INITIAL_REQUEST)
        session_id = request.get('session_id')
        imsi = request.get('subscription_id', {}).get('imsi')
        
        if request_type == RequestType.INITIAL_REQUEST:
            return self._handle_initial_request(request)
        elif request_type == RequestType.UPDATE_REQUEST:
            return self._handle_update_request(request)
        elif request_type == RequestType.TERMINATION_REQUEST:
            return self._handle_termination_request(request)
        elif request_type == RequestType.EVENT_REQUEST:
            return self._handle_event_request(request)
        else:
            return self._create_error_response(request, ResultCode.RATING_FAILED)
    
    def _handle_initial_request(self, request: Dict) -> Dict:
        """
        Handle initial CCR (session start)
        
        Args:
            request: CCR-I message
            
        Returns:
            CCA-I response
        """
        session_id = request.get('session_id')
        imsi = request.get('subscription_id', {}).get('imsi')
        msisdn = request.get('subscription_id', {}).get('msisdn')
        
        # Get subscriber balance
        balance = self._get_subscriber_balance(imsi)
        
        if balance <= 0:
            return self._create_error_response(request, ResultCode.CREDIT_LIMIT_REACHED)
        
        # Determine charging type
        charging_type = self._get_charging_type(imsi)
        
        # Create charging session
        session = ChargingSession(
            session_id=session_id,
            imsi=imsi,
            msisdn=msisdn,
            charging_type=charging_type,
            initial_balance=balance,
            current_balance=balance,
            apn=request.get('service_information', {}).get('apn')
        )
        
        # Calculate and grant initial quota
        service_type = request.get('service_identifier', 'data')
        requested_units = request.get('requested_service_unit', {})
        
        granted_units = self._calculate_granted_units(
            session,
            service_type,
            requested_units
        )
        
        if not granted_units:
            return self._create_error_response(request, ResultCode.CREDIT_LIMIT_REACHED)
        
        # Reserve quota
        self._reserve_quota(session, granted_units)
        
        # Store session
        self.sessions[session_id] = session
        
        # Create response
        response = {
            'result_code': ResultCode.SUCCESS,
            'session_id': session_id,
            'cc_request_type': RequestType.INITIAL_REQUEST,
            'granted_service_unit': granted_units,
            'validity_time': 3600,  # 1 hour
        }
        
        self.logger.info(f"Initial request granted for session {session_id}, IMSI {imsi}")
        
        return response
    
    def _handle_update_request(self, request: Dict) -> Dict:
        """
        Handle update CCR (quota replenishment)
        
        Args:
            request: CCR-U message
            
        Returns:
            CCA-U response
        """
        session_id = request.get('session_id')
        
        session = self.sessions.get(session_id)
        if not session:
            return self._create_error_response(request, ResultCode.USER_UNKNOWN)
        
        # Process used units
        used_units = request.get('used_service_unit', {})
        self._process_used_units(session, used_units)
        
        # Check if balance sufficient
        if session.current_balance <= 0:
            return self._create_error_response(request, ResultCode.CREDIT_LIMIT_REACHED)
        
        # Calculate and grant new quota
        service_type = request.get('service_identifier', 'data')
        requested_units = request.get('requested_service_unit', {})
        
        granted_units = self._calculate_granted_units(
            session,
            service_type,
            requested_units
        )
        
        if granted_units:
            self._reserve_quota(session, granted_units)
        
        response = {
            'result_code': ResultCode.SUCCESS,
            'session_id': session_id,
            'cc_request_type': RequestType.UPDATE_REQUEST,
            'granted_service_unit': granted_units,
            'validity_time': 3600,
        }
        
        session.last_update = datetime.now()
        
        return response
    
    def _handle_termination_request(self, request: Dict) -> Dict:
        """
        Handle termination CCR (session end)
        
        Args:
            request: CCR-T message
            
        Returns:
            CCA-T response
        """
        session_id = request.get('session_id')
        
        session = self.sessions.get(session_id)
        if not session:
            return self._create_error_response(request, ResultCode.USER_UNKNOWN)
        
        # Process final used units
        used_units = request.get('used_service_unit', {})
        self._process_used_units(session, used_units)
        
        # Release reserved quota
        self._release_reserved_quota(session)
        
        # Update final balance in database
        self._update_subscriber_balance(session.imsi, session.current_balance)
        
        # Remove session
        del self.sessions[session_id]
        
        response = {
            'result_code': ResultCode.SUCCESS,
            'session_id': session_id,
            'cc_request_type': RequestType.TERMINATION_REQUEST,
        }
        
        self.logger.info(f"Session terminated: {session_id}, IMSI {session.imsi}")
        
        return response
    
    def _handle_event_request(self, request: Dict) -> Dict:
        """
        Handle event CCR (one-time event)
        
        Args:
            request: CCR-E message
            
        Returns:
            CCA-E response
        """
        imsi = request.get('subscription_id', {}).get('imsi')
        
        # Process immediate charging (e.g., SMS)
        service_type = request.get('service_identifier', 'sms')
        requested_units = request.get('requested_service_unit', {})
        
        balance = self._get_subscriber_balance(imsi)
        cost = self._calculate_cost(service_type, requested_units)
        
        if balance < cost:
            return self._create_error_response(request, ResultCode.CREDIT_LIMIT_REACHED)
        
        # Deduct balance
        new_balance = balance - cost
        self._update_subscriber_balance(imsi, new_balance)
        
        response = {
            'result_code': ResultCode.SUCCESS,
            'session_id': request.get('session_id'),
            'cc_request_type': RequestType.EVENT_REQUEST,
            'granted_service_unit': requested_units,
            'cost': cost,
        }
        
        return response
    
    def _calculate_granted_units(self, session: ChargingSession, 
                                 service_type: str, requested_units: Dict) -> Dict:
        """
        Calculate granted quota based on balance and rating
        
        Args:
            session: Charging session
            service_type: Type of service
            requested_units: Requested quota
            
        Returns:
            Dictionary of granted units
        """
        granted = {}
        
        if service_type == 'data':
            # Calculate how much data can be granted
            requested_mb = requested_units.get('total_octets', 0) / (1024 * 1024)
            cost_per_mb = self._get_rate(service_type)
            
            affordable_mb = (session.current_balance - session.reserved_balance) / cost_per_mb
            granted_mb = min(requested_mb, affordable_mb, 100)  # Max 100MB per grant
            
            if granted_mb > 0:
                granted['total_octets'] = int(granted_mb * 1024 * 1024)
        
        elif service_type == 'voice':
            requested_minutes = requested_units.get('time', 0) / 60
            cost_per_minute = self._get_rate(service_type)
            
            affordable_minutes = (session.current_balance - session.reserved_balance) / cost_per_minute
            granted_minutes = min(requested_minutes, affordable_minutes, 60)  # Max 60 minutes
            
            if granted_minutes > 0:
                granted['time'] = int(granted_minutes * 60)
        
        elif service_type == 'sms':
            requested_count = requested_units.get('service_specific_units', 0)
            cost_per_sms = self._get_rate(service_type)
            
            affordable_count = int((session.current_balance - session.reserved_balance) / cost_per_sms)
            granted_count = min(requested_count, affordable_count, 10)  # Max 10 SMS
            
            if granted_count > 0:
                granted['service_specific_units'] = granted_count
        
        return granted
    
    def _process_used_units(self, session: ChargingSession, used_units: Dict):
        """
        Process used units and update balance
        
        Args:
            session: Charging session
            used_units: Used quota dictionary
        """
        # Data usage
        if 'total_octets' in used_units:
            bytes_used = used_units['total_octets']
            session.data_usage_bytes += bytes_used
            cost = self._calculate_cost('data', used_units)
            session.current_balance -= cost
        
        # Voice usage
        if 'time' in used_units:
            seconds_used = used_units['time']
            session.voice_usage_seconds += seconds_used
            cost = self._calculate_cost('voice', used_units)
            session.current_balance -= cost
        
        # SMS usage
        if 'service_specific_units' in used_units:
            sms_count = used_units['service_specific_units']
            session.sms_usage_count += sms_count
            cost = self._calculate_cost('sms', used_units)
            session.current_balance -= cost
    
    def _reserve_quota(self, session: ChargingSession, granted_units: Dict):
        """Reserve balance for granted quota"""
        cost = 0
        
        if 'total_octets' in granted_units:
            cost += self._calculate_cost('data', granted_units)
        if 'time' in granted_units:
            cost += self._calculate_cost('voice', granted_units)
        if 'service_specific_units' in granted_units:
            cost += self._calculate_cost('sms', granted_units)
        
        session.reserved_balance += cost
    
    def _release_reserved_quota(self, session: ChargingSession):
        """Release reserved balance"""
        session.reserved_balance = 0
    
    def _calculate_cost(self, service_type: str, units: Dict) -> float:
        """Calculate cost for given units"""
        rate = self._get_rate(service_type)
        
        if service_type == 'data':
            mb = units.get('total_octets', 0) / (1024 * 1024)
            return mb * rate
        elif service_type == 'voice':
            minutes = units.get('time', 0) / 60
            return minutes * rate
        elif service_type == 'sms':
            count = units.get('service_specific_units', 0)
            return count * rate
        
        return 0.0
    
    def _get_rate(self, service_type: str) -> float:
        """Get rate for service type"""
        for rule in self.rating_rules:
            if rule.service_type == service_type:
                return rule.cost_per_unit
        return 0.0
    
    def _get_subscriber_balance(self, imsi: str) -> float:
        """Get subscriber balance from database"""
        # Simplified - would query actual billing database
        return 10.0  # Default $10 balance
    
    def _update_subscriber_balance(self, imsi: str, balance: float):
        """Update subscriber balance in database"""
        self.logger.info(f"Updated balance for {imsi}: ${balance:.2f}")
    
    def _get_charging_type(self, imsi: str) -> ChargingType:
        """Get charging type for subscriber"""
        # Simplified - would check subscriber profile
        return ChargingType.PREPAID
    
    def _create_error_response(self, request: Dict, error_code: ResultCode) -> Dict:
        """Create error response"""
        return {
            'result_code': error_code,
            'session_id': request.get('session_id'),
            'cc_request_type': request.get('cc_request_type'),
        }
    
    def get_session(self, session_id: str) -> Optional[ChargingSession]:
        """Get charging session by ID"""
        return self.sessions.get(session_id)
    
    def list_active_sessions(self) -> List[ChargingSession]:
        """List all active charging sessions"""
        return list(self.sessions.values())
