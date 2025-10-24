"""
DRA main entry point
"""
import sys
import logging
import yaml
import argparse
import asyncio

from hlr_hss.dra import DiameterRoutingAgent, Peer, RoutingRule, RoutingAlgorithm


def setup_logging(config: dict):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    
    level = getattr(logging, log_config.get('level', 'INFO'))
    format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=level,
        format=format_str
    )


def load_config(config_file: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


async def main():
    """Main entry point for DRA"""
    parser = argparse.ArgumentParser(description='Diameter Routing Agent (DRA)')
    parser.add_argument(
        '-c', '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Diameter Routing Agent (DRA) Starting")
    logger.info("="*60)
    
    # Initialize DRA
    dra_config = config.get('dra', {})
    
    host = dra_config.get('host', 'dra.opennetwork.local')
    realm = dra_config.get('realm', 'opennetwork.local')
    bind_address = dra_config.get('bind_address', '0.0.0.0')
    port = dra_config.get('port', 3868)
    
    dra = DiameterRoutingAgent(host, realm, bind_address, port)
    
    # Add peers from configuration
    for peer_config in dra_config.get('peers', []):
        peer = Peer(
            host=peer_config['host'],
            realm=peer_config['realm'],
            address=peer_config['address'],
            port=peer_config.get('port', 3868),
            weight=peer_config.get('weight', 100),
            priority=peer_config.get('priority', 1),
            supported_applications=peer_config.get('applications', [])
        )
        dra.add_peer(peer)
    
    # Add routing rules from configuration
    for rule_config in dra_config.get('routing_rules', []):
        algorithm_str = rule_config.get('algorithm', 'round_robin')
        algorithm = RoutingAlgorithm(algorithm_str)
        
        rule = RoutingRule(
            name=rule_config['name'],
            application_id=rule_config.get('application_id'),
            command_code=rule_config.get('command_code'),
            target_realm=rule_config.get('target_realm'),
            target_hosts=rule_config.get('target_hosts', []),
            algorithm=algorithm,
            priority=rule_config.get('priority', 0)
        )
        dra.add_routing_rule(rule)
    
    logger.info(f"DRA listening on {bind_address}:{port}")
    logger.info("="*60)
    logger.info("DRA is ready!")
    logger.info("="*60)
    
    # Start DRA server
    try:
        await dra.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == '__main__':
    asyncio.run(main())
