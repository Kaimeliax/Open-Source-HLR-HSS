"""
Diameter Routing Agent (DRA)
Routes Diameter messages between network elements
Implements load balancing, failover, and routing rules
"""
import logging
import asyncio
import socket
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..diameter.diameter import DiameterMessage, DiameterAVPCode

logger = logging.getLogger(__name__)


class RoutingAlgorithm(Enum):
    """Routing algorithms"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    PRIORITY = "priority"


@dataclass
class Peer:
    """Diameter peer configuration"""
    host: str
    realm: str
    address: str
    port: int
    
    # Connection state
    connected: bool = False
    active_connections: int = 0
    
    # Routing configuration
    weight: int = 100
    priority: int = 1
    
    # Capabilities
    supported_applications: List[int] = None
    vendor_id: Optional[int] = None
    
    def __post_init__(self):
        if self.supported_applications is None:
            self.supported_applications = []


@dataclass
class RoutingRule:
    """Diameter routing rule"""
    name: str
    
    # Match conditions
    origin_host: Optional[str] = None
    origin_realm: Optional[str] = None
    destination_host: Optional[str] = None
    destination_realm: Optional[str] = None
    application_id: Optional[int] = None
    command_code: Optional[int] = None
    
    # Routing action
    target_realm: Optional[str] = None
    target_hosts: List[str] = None
    algorithm: RoutingAlgorithm = RoutingAlgorithm.ROUND_ROBIN
    
    # Priority (higher = more priority)
    priority: int = 0
    
    def __post_init__(self):
        if self.target_hosts is None:
            self.target_hosts = []
    
    def matches(self, msg: DiameterMessage) -> bool:
        """Check if message matches this rule"""
        # Extract AVPs for matching
        origin_host_avp = msg.get_avp(DiameterAVPCode.ORIGIN_HOST)
        origin_realm_avp = msg.get_avp(DiameterAVPCode.ORIGIN_REALM)
        dest_host_avp = msg.get_avp(DiameterAVPCode.DESTINATION_HOST)
        dest_realm_avp = msg.get_avp(DiameterAVPCode.DESTINATION_REALM)
        
        # Check each condition
        if self.origin_host and origin_host_avp:
            if origin_host_avp.data.decode('utf-8') != self.origin_host:
                return False
        
        if self.origin_realm and origin_realm_avp:
            if origin_realm_avp.data.decode('utf-8') != self.origin_realm:
                return False
        
        if self.destination_host and dest_host_avp:
            if dest_host_avp.data.decode('utf-8') != self.destination_host:
                return False
        
        if self.destination_realm and dest_realm_avp:
            if dest_realm_avp.data.decode('utf-8') != self.destination_realm:
                return False
        
        if self.application_id and msg.application_id != self.application_id:
            return False
        
        if self.command_code and msg.command_code != self.command_code:
            return False
        
        return True


class DiameterRoutingAgent:
    """
    Diameter Routing Agent (DRA)
    Routes Diameter messages between peers
    """
    
    def __init__(self, host: str, realm: str, bind_address: str = "0.0.0.0", port: int = 3868):
        """
        Initialize DRA
        
        Args:
            host: DRA host identity
            realm: DRA realm
            bind_address: Address to bind to
            port: Port to listen on
        """
        self.host = host
        self.realm = realm
        self.bind_address = bind_address
        self.port = port
        
        self.peers: Dict[str, Peer] = {}
        self.routing_rules: List[RoutingRule] = []
        
        # Routing state
        self.round_robin_index: Dict[str, int] = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DRA initialized: {host}@{realm}")
    
    def add_peer(self, peer: Peer):
        """
        Add Diameter peer
        
        Args:
            peer: Peer configuration
        """
        peer_id = f"{peer.host}@{peer.realm}"
        self.peers[peer_id] = peer
        self.logger.info(f"Added peer: {peer_id}")
    
    def remove_peer(self, host: str, realm: str):
        """
        Remove Diameter peer
        
        Args:
            host: Peer host
            realm: Peer realm
        """
        peer_id = f"{host}@{realm}"
        if peer_id in self.peers:
            del self.peers[peer_id]
            self.logger.info(f"Removed peer: {peer_id}")
    
    def add_routing_rule(self, rule: RoutingRule):
        """
        Add routing rule
        
        Args:
            rule: Routing rule
        """
        self.routing_rules.append(rule)
        # Sort rules by priority (descending)
        self.routing_rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"Added routing rule: {rule.name}")
    
    def remove_routing_rule(self, name: str):
        """
        Remove routing rule by name
        
        Args:
            name: Rule name
        """
        self.routing_rules = [r for r in self.routing_rules if r.name != name]
        self.logger.info(f"Removed routing rule: {name}")
    
    def route_message(self, msg: DiameterMessage) -> Optional[List[Peer]]:
        """
        Route Diameter message to appropriate peer(s)
        
        Args:
            msg: Diameter message to route
            
        Returns:
            List of target peers or None if no route found
        """
        # Find matching routing rule
        matching_rule = None
        for rule in self.routing_rules:
            if rule.matches(msg):
                matching_rule = rule
                break
        
        if not matching_rule:
            self.logger.warning("No matching routing rule found")
            return None
        
        # Get candidate peers
        candidate_peers = []
        for host in matching_rule.target_hosts:
            # Find peer by host
            for peer_id, peer in self.peers.items():
                if peer.host == host and peer.connected:
                    candidate_peers.append(peer)
        
        if not candidate_peers:
            self.logger.warning("No available peers for routing")
            return None
        
        # Apply routing algorithm
        selected_peers = self._apply_routing_algorithm(
            candidate_peers,
            matching_rule.algorithm,
            matching_rule.name
        )
        
        return selected_peers
    
    def _apply_routing_algorithm(self, peers: List[Peer], 
                                 algorithm: RoutingAlgorithm,
                                 rule_name: str) -> List[Peer]:
        """
        Apply routing algorithm to select peer(s)
        
        Args:
            peers: Candidate peers
            algorithm: Routing algorithm
            rule_name: Name of routing rule (for state tracking)
            
        Returns:
            List of selected peers
        """
        if algorithm == RoutingAlgorithm.ROUND_ROBIN:
            return self._round_robin(peers, rule_name)
        
        elif algorithm == RoutingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections(peers)
        
        elif algorithm == RoutingAlgorithm.WEIGHTED:
            return self._weighted_selection(peers)
        
        elif algorithm == RoutingAlgorithm.PRIORITY:
            return self._priority_selection(peers)
        
        else:
            # Default to first peer
            return [peers[0]]
    
    def _round_robin(self, peers: List[Peer], rule_name: str) -> List[Peer]:
        """Round-robin peer selection"""
        if rule_name not in self.round_robin_index:
            self.round_robin_index[rule_name] = 0
        
        index = self.round_robin_index[rule_name]
        selected = peers[index % len(peers)]
        
        self.round_robin_index[rule_name] = (index + 1) % len(peers)
        
        return [selected]
    
    def _least_connections(self, peers: List[Peer]) -> List[Peer]:
        """Select peer with least active connections"""
        selected = min(peers, key=lambda p: p.active_connections)
        return [selected]
    
    def _weighted_selection(self, peers: List[Peer]) -> List[Peer]:
        """Weighted peer selection based on peer weights"""
        import random
        
        total_weight = sum(p.weight for p in peers)
        if total_weight == 0:
            return [peers[0]]
        
        rand = random.randint(0, total_weight - 1)
        
        cumulative = 0
        for peer in peers:
            cumulative += peer.weight
            if rand < cumulative:
                return [peer]
        
        return [peers[-1]]
    
    def _priority_selection(self, peers: List[Peer]) -> List[Peer]:
        """Select peer(s) with highest priority"""
        max_priority = max(p.priority for p in peers)
        high_priority_peers = [p for p in peers if p.priority == max_priority]
        
        # Return first high priority peer
        return [high_priority_peers[0]]
    
    async def handle_connection(self, reader: asyncio.StreamReader, 
                               writer: asyncio.StreamWriter):
        """
        Handle incoming Diameter connection
        
        Args:
            reader: Stream reader
            writer: Stream writer
        """
        addr = writer.get_extra_info('peername')
        self.logger.info(f"New connection from {addr}")
        
        try:
            while True:
                # Read Diameter message header (20 bytes)
                header = await reader.read(20)
                if not header:
                    break
                
                # Parse message length
                length_bytes = bytes([0]) + header[1:4]
                msg_length = int.from_bytes(length_bytes, 'big')
                
                # Read rest of message
                remaining = msg_length - 20
                body = await reader.read(remaining)
                
                # Parse message
                msg_data = header + body
                msg = DiameterMessage.from_bytes(msg_data)
                
                self.logger.debug(f"Received message: cmd={msg.command_code}, app={msg.application_id}")
                
                # Route message
                target_peers = self.route_message(msg)
                
                if target_peers:
                    # Forward to selected peer(s)
                    for peer in target_peers:
                        await self._forward_message(msg, peer)
                else:
                    self.logger.warning("Unable to route message")
                
        except Exception as e:
            self.logger.error(f"Error handling connection: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.logger.info(f"Connection closed from {addr}")
    
    async def _forward_message(self, msg: DiameterMessage, peer: Peer):
        """
        Forward message to peer
        
        Args:
            msg: Diameter message
            peer: Target peer
        """
        try:
            reader, writer = await asyncio.open_connection(peer.address, peer.port)
            
            # Send message
            msg_bytes = msg.to_bytes()
            writer.write(msg_bytes)
            await writer.drain()
            
            # If request, wait for answer
            if msg.request:
                # Read response
                header = await reader.read(20)
                if header:
                    length_bytes = bytes([0]) + header[1:4]
                    msg_length = int.from_bytes(length_bytes, 'big')
                    remaining = msg_length - 20
                    body = await reader.read(remaining)
                    
                    # Response would be sent back to original sender
                    # (simplified - would need connection tracking)
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            self.logger.error(f"Error forwarding to {peer.host}: {e}")
    
    async def start(self):
        """Start DRA server"""
        server = await asyncio.start_server(
            self.handle_connection,
            self.bind_address,
            self.port
        )
        
        addr = server.sockets[0].getsockname()
        self.logger.info(f"DRA listening on {addr}")
        
        async with server:
            await server.serve_forever()
    
    def get_peer_status(self) -> Dict[str, Dict]:
        """Get status of all peers"""
        status = {}
        for peer_id, peer in self.peers.items():
            status[peer_id] = {
                'connected': peer.connected,
                'active_connections': peer.active_connections,
                'address': peer.address,
                'port': peer.port,
                'weight': peer.weight,
                'priority': peer.priority,
            }
        return status
    
    def get_routing_rules(self) -> List[Dict]:
        """Get all routing rules"""
        return [
            {
                'name': rule.name,
                'application_id': rule.application_id,
                'command_code': rule.command_code,
                'target_realm': rule.target_realm,
                'target_hosts': rule.target_hosts,
                'algorithm': rule.algorithm.value,
                'priority': rule.priority,
            }
            for rule in self.routing_rules
        ]
