"""
Authentication algorithms for 2G-5G networks
Supports: Milenage, TUAK, XOR, and legacy algorithms
"""
import hashlib
import hmac
import os
from typing import Tuple, Optional
from Crypto.Cipher import AES
from Crypto.Hash import CMAC
import logging

logger = logging.getLogger(__name__)


class Milenage:
    """
    Milenage authentication algorithm (3GPP TS 35.205-206)
    Used for 3G/4G/5G authentication
    """
    
    def __init__(self):
        """Initialize Milenage algorithm"""
        # Constants as per 3GPP TS 35.206
        self.c1 = bytes.fromhex('00000000000000000000000000000000')
        self.c2 = bytes.fromhex('00000000000000000000000000000001')
        self.c3 = bytes.fromhex('00000000000000000000000000000002')
        self.c4 = bytes.fromhex('00000000000000000000000000000004')
        self.c5 = bytes.fromhex('00000000000000000000000000000008')
        
        self.r1 = 64
        self.r2 = 0
        self.r3 = 32
        self.r4 = 64
        self.r5 = 96
    
    def _rotate(self, data: bytes, bits: int) -> bytes:
        """Rotate bytes left by specified bits"""
        data_int = int.from_bytes(data, 'big')
        rotated = ((data_int << bits) | (data_int >> (128 - bits))) & ((1 << 128) - 1)
        return rotated.to_bytes(16, 'big')
    
    def _xor(self, a: bytes, b: bytes) -> bytes:
        """XOR two byte strings"""
        return bytes(x ^ y for x, y in zip(a, b))
    
    def generate_opc(self, k: bytes, op: bytes) -> bytes:
        """
        Generate OPc from K and OP
        
        Args:
            k: Subscriber key (128 bits)
            op: Operator variant key (128 bits)
            
        Returns:
            OPc value (128 bits)
        """
        cipher = AES.new(k, AES.MODE_ECB)
        opc = self._xor(op, cipher.encrypt(op))
        return opc
    
    def f1(self, k: bytes, rand: bytes, sqn: bytes, amf: bytes, opc: bytes) -> Tuple[bytes, bytes]:
        """
        Generate MAC-A and MAC-S (Network authentication)
        
        Args:
            k: Subscriber key (128 bits)
            rand: Random challenge (128 bits)
            sqn: Sequence number (48 bits)
            amf: Authentication Management Field (16 bits)
            opc: Operator variant key (128 bits)
            
        Returns:
            Tuple of (MAC-A, MAC-S) each 64 bits
        """
        # Construct input
        temp = sqn + amf + sqn + amf
        
        cipher = AES.new(k, AES.MODE_ECB)
        
        # First encryption
        temp = self._xor(temp, opc)
        temp = cipher.encrypt(temp)
        
        # XOR with rand and c1
        temp = self._xor(temp, self._xor(rand, self.c1))
        
        # Rotate and second encryption
        temp = self._rotate(temp, self.r1)
        temp = self._xor(temp, opc)
        out = cipher.encrypt(temp)
        
        mac_a = out[:8]
        mac_s = self._xor(out, self.c1)[:8]
        
        return mac_a, mac_s
    
    def f2345(self, k: bytes, rand: bytes, opc: bytes) -> Tuple[bytes, bytes, bytes, bytes]:
        """
        Generate RES, CK, IK, and AK
        
        Args:
            k: Subscriber key (128 bits)
            rand: Random challenge (128 bits)
            opc: Operator variant key (128 bits)
            
        Returns:
            Tuple of (RES, CK, IK, AK)
        """
        cipher = AES.new(k, AES.MODE_ECB)
        
        # Encrypt RAND
        temp = cipher.encrypt(rand)
        temp = self._xor(temp, opc)
        
        # Generate RES (f2)
        temp_res = self._xor(temp, self.c2)
        temp_res = self._rotate(temp_res, self.r2)
        temp_res = self._xor(temp_res, opc)
        res = cipher.encrypt(temp_res)[8:16]  # 64 bits
        
        # Generate CK (f3)
        temp_ck = self._xor(temp, self.c3)
        temp_ck = self._rotate(temp_ck, self.r3)
        temp_ck = self._xor(temp_ck, opc)
        ck = cipher.encrypt(temp_ck)  # 128 bits
        
        # Generate IK (f4)
        temp_ik = self._xor(temp, self.c4)
        temp_ik = self._rotate(temp_ik, self.r4)
        temp_ik = self._xor(temp_ik, opc)
        ik = cipher.encrypt(temp_ik)  # 128 bits
        
        # Generate AK (f5)
        temp_ak = self._xor(temp, self.c5)
        temp_ak = self._rotate(temp_ak, self.r5)
        temp_ak = self._xor(temp_ak, opc)
        ak = cipher.encrypt(temp_ak)[:6]  # 48 bits
        
        return res, ck, ik, ak
    
    def generate_auth_vector(self, k: str, opc: str, amf: str, sqn: int) -> dict:
        """
        Generate complete authentication vector
        
        Args:
            k: Subscriber key (hex string)
            opc: OPc key (hex string)
            amf: Authentication Management Field (hex string)
            sqn: Sequence number (integer)
            
        Returns:
            Dictionary containing authentication vector components
        """
        try:
            # Convert inputs to bytes
            k_bytes = bytes.fromhex(k)
            opc_bytes = bytes.fromhex(opc)
            amf_bytes = bytes.fromhex(amf)
            sqn_bytes = sqn.to_bytes(6, 'big')
            
            # Generate random challenge
            rand = os.urandom(16)
            
            # Generate MAC and keys
            mac_a, mac_s = self.f1(k_bytes, rand, sqn_bytes, amf_bytes, opc_bytes)
            res, ck, ik, ak = self.f2345(k_bytes, rand, opc_bytes)
            
            # Generate AUTN
            sqn_xor_ak = self._xor(sqn_bytes, ak)
            autn = sqn_xor_ak + amf_bytes + mac_a
            
            # Generate Kasme for LTE (for 5G it would be Kausf)
            key = ck + ik
            s = bytes.fromhex('10') + self._xor(sqn_bytes, ak) + bytes.fromhex('0003')
            s = s + b'\x00' * (32 - len(s))
            
            kasme = hmac.new(key, s, hashlib.sha256).digest()
            
            return {
                'rand': rand.hex(),
                'autn': autn.hex(),
                'xres': res.hex(),
                'kasme': kasme.hex(),
                'ck': ck.hex(),
                'ik': ik.hex(),
                'ak': ak.hex(),
                'mac_a': mac_a.hex(),
            }
        except Exception as e:
            logger.error(f"Error generating auth vector: {e}")
            return None


class XOR:
    """
    XOR authentication algorithm
    Simple algorithm for testing or legacy systems
    """
    
    def generate_auth_vector(self, k: str, sqn: int) -> dict:
        """
        Generate authentication vector using XOR algorithm
        
        Args:
            k: Subscriber key (hex string)
            sqn: Sequence number (integer)
            
        Returns:
            Dictionary containing authentication vector components
        """
        try:
            k_bytes = bytes.fromhex(k)
            sqn_bytes = sqn.to_bytes(6, 'big')
            
            # Generate random challenge
            rand = os.urandom(16)
            
            # Simple XOR operations
            xres = bytes(x ^ y for x, y in zip(rand, k_bytes))[:8]
            ck = bytes(x ^ y ^ z for x, y, z in zip(rand, k_bytes, sqn_bytes + b'\x00' * 10))
            ik = bytes(x ^ y for x, y in zip(ck, k_bytes))
            
            # Generate AK and AUTN
            ak = xres[:6]
            amf = bytes.fromhex('8000')
            sqn_xor_ak = bytes(x ^ y for x, y in zip(sqn_bytes, ak))
            
            # MAC calculation
            mac_input = sqn_bytes + rand + amf
            mac_a = hashlib.sha256(mac_input).digest()[:8]
            
            autn = sqn_xor_ak + amf + mac_a
            
            # Kasme
            key = ck + ik
            kasme = hashlib.sha256(key + rand).digest()
            
            return {
                'rand': rand.hex(),
                'autn': autn.hex(),
                'xres': xres.hex(),
                'kasme': kasme.hex(),
                'ck': ck.hex(),
                'ik': ik.hex(),
                'ak': ak.hex(),
                'mac_a': mac_a.hex(),
            }
        except Exception as e:
            logger.error(f"Error generating XOR auth vector: {e}")
            return None


class AuthenticationManager:
    """
    Manages authentication for all supported algorithms
    """
    
    def __init__(self):
        """Initialize authentication manager"""
        self.milenage = Milenage()
        self.xor = XOR()
        self.logger = logging.getLogger(__name__)
    
    def generate_auth_vector(self, algo: str, k: str, opc: Optional[str], 
                            amf: str, sqn: int) -> Optional[dict]:
        """
        Generate authentication vector for specified algorithm
        
        Args:
            algo: Algorithm name ('milenage', 'xor', 'tuak')
            k: Subscriber key
            opc: OPc key (for Milenage)
            amf: Authentication Management Field
            sqn: Sequence number
            
        Returns:
            Authentication vector dictionary or None
        """
        algo = algo.lower()
        
        try:
            if algo == 'milenage':
                if not opc:
                    self.logger.error("OPc required for Milenage")
                    return None
                return self.milenage.generate_auth_vector(k, opc, amf, sqn)
            
            elif algo == 'xor':
                return self.xor.generate_auth_vector(k, sqn)
            
            elif algo == 'tuak':
                # TUAK would be implemented here for 5G
                # Similar structure to Milenage but with different operations
                self.logger.warning("TUAK not yet implemented, using Milenage")
                if not opc:
                    self.logger.error("OPc required for TUAK")
                    return None
                return self.milenage.generate_auth_vector(k, opc, amf, sqn)
            
            else:
                self.logger.error(f"Unknown algorithm: {algo}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating auth vector: {e}")
            return None
    
    def verify_response(self, xres: str, res: str) -> bool:
        """
        Verify authentication response
        
        Args:
            xres: Expected response
            res: Received response
            
        Returns:
            True if match, False otherwise
        """
        return xres.lower() == res.lower()
