"""
Diameter protocol handling for 3G/4G/5G networks
Implements S6a (MME-HSS), S6d (SGSN-HSS), Cx/Dx (CSCF-HSS), and 5G interfaces
"""
import logging
import struct
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum

logger = logging.getLogger(__name__)


class DiameterCommandCode(IntEnum):
    """Diameter Command Codes"""
    # Base Protocol
    CAPABILITIES_EXCHANGE = 257
    RE_AUTH = 258
    ACCOUNTING = 271
    ABORT_SESSION = 274
    SESSION_TERMINATION = 275
    DEVICE_WATCHDOG = 280
    DISCONNECT_PEER = 282
    
    # S6a/S6d Interface (3GPP TS 29.272)
    UPDATE_LOCATION = 316
    CANCEL_LOCATION = 317
    AUTHENTICATION_INFORMATION = 318
    INSERT_SUBSCRIBER_DATA = 319
    DELETE_SUBSCRIBER_DATA = 320
    PURGE_UE = 321
    RESET = 322
    NOTIFY = 323
    
    # Cx/Dx Interface (3GPP TS 29.229)
    USER_AUTHORIZATION = 300
    SERVER_ASSIGNMENT = 301
    LOCATION_INFO = 302
    MULTIMEDIA_AUTH = 303
    REGISTRATION_TERMINATION = 304
    PUSH_PROFILE = 305


class DiameterApplicationId(IntEnum):
    """Diameter Application IDs"""
    DIAMETER_BASE = 0
    NASREQ = 1
    MOBILE_IP = 2
    DIAMETER_BASE_ACCOUNTING = 3
    RELAY = 0xffffffff
    
    # 3GPP Applications
    S6A_S6D = 16777251
    S13 = 16777252
    SLG = 16777255
    CX_DX = 16777216
    SH = 16777217
    GX = 16777238
    RX = 16777236


class DiameterAVPCode(IntEnum):
    """Diameter AVP Codes"""
    # Base Protocol AVPs
    USER_NAME = 1
    RESULT_CODE = 268
    VENDOR_ID = 266
    AUTH_APPLICATION_ID = 258
    ACCT_APPLICATION_ID = 259
    ORIGIN_HOST = 264
    ORIGIN_REALM = 296
    DESTINATION_HOST = 293
    DESTINATION_REALM = 283
    SESSION_ID = 263
    
    # 3GPP AVPs
    VISITED_PLMN_ID = 1407
    RAT_TYPE = 1032
    ULR_FLAGS = 1405
    ULA_FLAGS = 1406
    SUBSCRIPTION_DATA = 1400
    AUTHENTICATION_INFO = 1413
    REQUESTED_EUTRAN_AUTH_INFO = 1408
    E_UTRAN_VECTOR = 1414
    RAND = 1447
    XRES = 1448
    AUTN = 1449
    KASME = 1450


@dataclass
class DiameterAVP:
    """Diameter Attribute-Value Pair"""
    code: int
    vendor_id: int = 0
    mandatory: bool = False
    protected: bool = False
    data: bytes = b''
    
    def to_bytes(self) -> bytes:
        """Convert AVP to bytes"""
        flags = 0
        if self.vendor_id:
            flags |= 0x80  # V-bit
        if self.mandatory:
            flags |= 0x40  # M-bit
        if self.protected:
            flags |= 0x20  # P-bit
        
        avp_header = struct.pack('!IBB', self.code, flags, 0)
        
        if self.vendor_id:
            avp_header += struct.pack('!I', self.vendor_id)
        
        avp_length = len(avp_header) + len(self.data) + 4
        avp_bytes = avp_header + self.data
        
        # Add padding to 4-byte boundary
        padding = (4 - (len(avp_bytes) % 4)) % 4
        avp_bytes += b'\x00' * padding
        
        # Update length field
        avp_bytes = avp_bytes[:4] + struct.pack('!I', avp_length)[1:] + avp_bytes[7:]
        
        return avp_bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple['DiameterAVP', int]:
        """Parse AVP from bytes"""
        code = struct.unpack('!I', data[0:4])[0]
        flags = data[4]
        length_bytes = bytes([0]) + data[5:8]
        length = struct.unpack('!I', length_bytes)[0]
        
        has_vendor = bool(flags & 0x80)
        mandatory = bool(flags & 0x40)
        protected = bool(flags & 0x20)
        
        offset = 8
        vendor_id = 0
        
        if has_vendor:
            vendor_id = struct.unpack('!I', data[offset:offset+4])[0]
            offset += 4
        
        data_length = length - offset
        avp_data = data[offset:offset+data_length]
        
        # Calculate padding
        padding = (4 - (length % 4)) % 4
        total_length = length + padding
        
        avp = cls(
            code=code,
            vendor_id=vendor_id,
            mandatory=mandatory,
            protected=protected,
            data=avp_data
        )
        
        return avp, total_length


@dataclass
class DiameterMessage:
    """Diameter Message"""
    version: int = 1
    command_code: int = 0
    application_id: int = 0
    hop_by_hop_id: int = 0
    end_to_end_id: int = 0
    request: bool = True
    proxyable: bool = True
    error: bool = False
    retransmit: bool = False
    avps: List[DiameterAVP] = None
    
    def __post_init__(self):
        if self.avps is None:
            self.avps = []
    
    def add_avp(self, avp: DiameterAVP):
        """Add AVP to message"""
        self.avps.append(avp)
    
    def get_avp(self, code: int, vendor_id: int = 0) -> Optional[DiameterAVP]:
        """Get AVP by code"""
        for avp in self.avps:
            if avp.code == code and avp.vendor_id == vendor_id:
                return avp
        return None
    
    def to_bytes(self) -> bytes:
        """Convert message to bytes"""
        # Build flags
        flags = 0
        if self.request:
            flags |= 0x80  # R-bit
        if self.proxyable:
            flags |= 0x40  # P-bit
        if self.error:
            flags |= 0x20  # E-bit
        if self.retransmit:
            flags |= 0x10  # T-bit
        
        # Serialize AVPs
        avp_data = b''
        for avp in self.avps:
            avp_data += avp.to_bytes()
        
        # Calculate total length
        length = 20 + len(avp_data)
        
        # Build header
        header = struct.pack('!BBHIII',
                           self.version,
                           flags,
                           self.command_code,
                           self.application_id,
                           self.hop_by_hop_id,
                           self.end_to_end_id)
        
        # Update length in header
        msg_bytes = header[:1] + struct.pack('!I', length)[1:] + header[4:] + avp_data
        
        return msg_bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'DiameterMessage':
        """Parse message from bytes"""
        version = data[0]
        length_bytes = bytes([0]) + data[1:4]
        length = struct.unpack('!I', length_bytes)[0]
        flags = data[1]
        command_code = struct.unpack('!I', bytes([0]) + data[4:7])[0]
        application_id = struct.unpack('!I', data[8:12])[0]
        hop_by_hop_id = struct.unpack('!I', data[12:16])[0]
        end_to_end_id = struct.unpack('!I', data[16:20])[0]
        
        request = bool(flags & 0x80)
        proxyable = bool(flags & 0x40)
        error = bool(flags & 0x20)
        retransmit = bool(flags & 0x10)
        
        msg = cls(
            version=version,
            command_code=command_code,
            application_id=application_id,
            hop_by_hop_id=hop_by_hop_id,
            end_to_end_id=end_to_end_id,
            request=request,
            proxyable=proxyable,
            error=error,
            retransmit=retransmit
        )
        
        # Parse AVPs
        offset = 20
        while offset < length:
            avp, avp_length = DiameterAVP.from_bytes(data[offset:])
            msg.add_avp(avp)
            offset += avp_length
        
        return msg


class DiameterS6aInterface:
    """
    S6a interface implementation (MME-HSS)
    3GPP TS 29.272
    """
    
    def __init__(self, hlr_hss, auth_manager):
        """
        Initialize S6a interface
        
        Args:
            hlr_hss: HLR_HSS instance
            auth_manager: AuthenticationManager instance
        """
        self.hlr_hss = hlr_hss
        self.auth_manager = auth_manager
        self.logger = logging.getLogger(__name__)
    
    def handle_authentication_information_request(self, msg: DiameterMessage) -> DiameterMessage:
        """
        Handle Authentication-Information-Request (AIR)
        
        Args:
            msg: AIR Diameter message
            
        Returns:
            Authentication-Information-Answer (AIA)
        """
        # Extract IMSI from User-Name AVP
        user_name_avp = msg.get_avp(DiameterAVPCode.USER_NAME)
        if not user_name_avp:
            return self._create_error_answer(msg, 5005)  # DIAMETER_MISSING_AVP
        
        imsi = user_name_avp.data.decode('utf-8')
        
        # Get subscriber
        subscriber = self.hlr_hss.get_subscriber(imsi)
        if not subscriber:
            return self._create_error_answer(msg, 5001)  # DIAMETER_ERROR_USER_UNKNOWN
        
        if not self.hlr_hss.is_subscriber_active(imsi):
            return self._create_error_answer(msg, 5004)  # DIAMETER_ERROR_USER_UNKNOWN
        
        # Generate authentication vectors
        num_vectors = 1  # Could be extracted from Requested-EUTRAN-Authentication-Info
        
        auth_vectors = []
        for i in range(num_vectors):
            sqn = subscriber.sqn + i
            auth_vec = self.auth_manager.generate_auth_vector(
                'milenage',
                subscriber.ki,
                subscriber.opc,
                subscriber.amf,
                sqn
            )
            
            if auth_vec:
                auth_vectors.append(auth_vec)
        
        # Update SQN
        self.hlr_hss.update_subscriber(imsi, {'sqn': subscriber.sqn + num_vectors})
        
        # Create answer message
        answer = self._create_answer(msg)
        
        # Add Authentication-Info AVP with E-UTRAN vectors
        if auth_vectors:
            auth_info_data = self._encode_authentication_info(auth_vectors)
            auth_info_avp = DiameterAVP(
                code=DiameterAVPCode.AUTHENTICATION_INFO,
                vendor_id=10415,  # 3GPP
                mandatory=True,
                data=auth_info_data
            )
            answer.add_avp(auth_info_avp)
        
        return answer
    
    def handle_update_location_request(self, msg: DiameterMessage) -> DiameterMessage:
        """
        Handle Update-Location-Request (ULR)
        
        Args:
            msg: ULR Diameter message
            
        Returns:
            Update-Location-Answer (ULA)
        """
        # Extract IMSI
        user_name_avp = msg.get_avp(DiameterAVPCode.USER_NAME)
        if not user_name_avp:
            return self._create_error_answer(msg, 5005)
        
        imsi = user_name_avp.data.decode('utf-8')
        
        # Get subscriber
        subscriber = self.hlr_hss.get_subscriber(imsi)
        if not subscriber:
            return self._create_error_answer(msg, 5001)
        
        # Extract Visited-PLMN-ID and check roaming
        visited_plmn_avp = msg.get_avp(DiameterAVPCode.VISITED_PLMN_ID, 10415)
        if visited_plmn_avp:
            visited_plmn = visited_plmn_avp.data.hex()
            if not self.hlr_hss.check_roaming_allowed(imsi, visited_plmn):
                return self._create_error_answer(msg, 5490)  # ROAMING_NOT_ALLOWED
        
        # Update location
        origin_host_avp = msg.get_avp(DiameterAVPCode.ORIGIN_HOST)
        if origin_host_avp:
            mme_host = origin_host_avp.data.decode('utf-8')
            self.hlr_hss.update_subscriber(imsi, {'serving_mme': mme_host})
        
        # Create answer with subscription data
        answer = self._create_answer(msg)
        
        # Add subscription data AVP
        sub_data = self._encode_subscription_data(subscriber)
        sub_data_avp = DiameterAVP(
            code=DiameterAVPCode.SUBSCRIPTION_DATA,
            vendor_id=10415,
            mandatory=True,
            data=sub_data
        )
        answer.add_avp(sub_data_avp)
        
        return answer
    
    def handle_purge_ue_request(self, msg: DiameterMessage) -> DiameterMessage:
        """
        Handle Purge-UE-Request (PUR)
        
        Args:
            msg: PUR Diameter message
            
        Returns:
            Purge-UE-Answer (PUA)
        """
        # Extract IMSI
        user_name_avp = msg.get_avp(DiameterAVPCode.USER_NAME)
        if not user_name_avp:
            return self._create_error_answer(msg, 5005)
        
        imsi = user_name_avp.data.decode('utf-8')
        
        # Clear serving MME
        self.hlr_hss.update_subscriber(imsi, {'serving_mme': None})
        
        return self._create_answer(msg)
    
    def _create_answer(self, request: DiameterMessage) -> DiameterMessage:
        """Create answer message from request"""
        answer = DiameterMessage(
            command_code=request.command_code,
            application_id=request.application_id,
            hop_by_hop_id=request.hop_by_hop_id,
            end_to_end_id=request.end_to_end_id,
            request=False,
            proxyable=request.proxyable
        )
        
        # Copy required AVPs
        session_id = request.get_avp(DiameterAVPCode.SESSION_ID)
        if session_id:
            answer.add_avp(session_id)
        
        # Add Result-Code (DIAMETER_SUCCESS = 2001)
        result_code_avp = DiameterAVP(
            code=DiameterAVPCode.RESULT_CODE,
            mandatory=True,
            data=struct.pack('!I', 2001)
        )
        answer.add_avp(result_code_avp)
        
        return answer
    
    def _create_error_answer(self, request: DiameterMessage, error_code: int) -> DiameterMessage:
        """Create error answer"""
        answer = self._create_answer(request)
        answer.error = True
        
        # Update result code
        result_code_avp = answer.get_avp(DiameterAVPCode.RESULT_CODE)
        if result_code_avp:
            result_code_avp.data = struct.pack('!I', error_code)
        
        return answer
    
    def _encode_authentication_info(self, auth_vectors: List[Dict]) -> bytes:
        """Encode authentication info AVP"""
        # Simplified encoding - would need proper AVP grouping
        data = b''
        for vec in auth_vectors:
            # E-UTRAN-Vector AVP would contain RAND, XRES, AUTN, KASME
            pass
        return data
    
    def _encode_subscription_data(self, subscriber) -> bytes:
        """Encode subscription data AVP"""
        # Simplified encoding - would contain AMBR, APN config, QoS, etc.
        data = b''
        return data


class DiameterCxInterface:
    """
    Cx/Dx interface implementation (CSCF-HSS)
    3GPP TS 29.229 - IMS HSS interface
    """
    
    def __init__(self, hlr_hss):
        """
        Initialize Cx interface
        
        Args:
            hlr_hss: HLR_HSS instance
        """
        self.hlr_hss = hlr_hss
        self.logger = logging.getLogger(__name__)
    
    def handle_user_authorization_request(self, msg: DiameterMessage) -> DiameterMessage:
        """
        Handle User-Authorization-Request (UAR)
        Used for IMS registration authorization
        """
        # Extract public identity
        user_name_avp = msg.get_avp(DiameterAVPCode.USER_NAME)
        if not user_name_avp:
            return self._create_error_answer(msg, 5005)
        
        public_identity = user_name_avp.data.decode('utf-8')
        
        # Authorize user (simplified)
        answer = self._create_answer(msg)
        
        return answer
    
    def handle_multimedia_auth_request(self, msg: DiameterMessage) -> DiameterMessage:
        """
        Handle Multimedia-Auth-Request (MAR)
        Used for IMS AKA authentication
        """
        user_name_avp = msg.get_avp(DiameterAVPCode.USER_NAME)
        if not user_name_avp:
            return self._create_error_answer(msg, 5005)
        
        answer = self._create_answer(msg)
        
        return answer
    
    def _create_answer(self, request: DiameterMessage) -> DiameterMessage:
        """Create answer message"""
        answer = DiameterMessage(
            command_code=request.command_code,
            application_id=request.application_id,
            hop_by_hop_id=request.hop_by_hop_id,
            end_to_end_id=request.end_to_end_id,
            request=False
        )
        
        result_code_avp = DiameterAVP(
            code=DiameterAVPCode.RESULT_CODE,
            mandatory=True,
            data=struct.pack('!I', 2001)
        )
        answer.add_avp(result_code_avp)
        
        return answer
    
    def _create_error_answer(self, request: DiameterMessage, error_code: int) -> DiameterMessage:
        """Create error answer"""
        answer = self._create_answer(request)
        answer.error = True
        
        result_code_avp = answer.get_avp(DiameterAVPCode.RESULT_CODE)
        if result_code_avp:
            result_code_avp.data = struct.pack('!I', error_code)
        
        return answer
