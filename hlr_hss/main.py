"""
Main entry point for HLR/HSS system
"""
import sys
import logging
import yaml
import argparse
from pathlib import Path

from hlr_hss.core import HLR_HSS, ENodeBProfile
from hlr_hss.database import create_database_handler
from hlr_hss.authentication import AuthenticationManager
from hlr_hss.ocs import OnlineChargingSystem
from hlr_hss.roaming import RoamingManager
from hlr_hss.api import create_api


def setup_logging(config: dict):
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    
    level = getattr(logging, log_config.get('level', 'INFO'))
    format_str = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handlers = []
    
    if log_config.get('console', True):
        handlers.append(logging.StreamHandler(sys.stdout))
    
    if log_config.get('file'):
        handlers.append(logging.FileHandler(log_config['file']))
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers
    )


def load_config(config_file: str) -> dict:
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Open Source HLR/HSS')
    parser.add_argument(
        '-c', '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database with sample data'
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
    logger.info("Open Source HLR/HSS Starting")
    logger.info("="*60)
    
    # Initialize database
    db_config = config.get('database', {})
    db_type = db_config.get('type', 'memory')
    
    logger.info(f"Initializing {db_type} database...")
    
    if db_type == 'memory':
        db_handler = create_database_handler('memory')
    elif db_type == 'postgresql':
        pg_config = db_config.get('postgresql', {})
        conn_str = f"postgresql://{pg_config['username']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
        db_handler = create_database_handler('postgresql', connection_string=conn_str)
    elif db_type == 'mysql':
        mysql_config = db_config.get('mysql', {})
        conn_str = f"mysql+mysqlconnector://{mysql_config['username']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
        db_handler = create_database_handler('mysql', connection_string=conn_str)
    elif db_type == 'mongodb':
        mongo_config = db_config.get('mongodb', {})
        conn_str = f"mongodb://{mongo_config['username']}:{mongo_config['password']}@{mongo_config['host']}:{mongo_config['port']}"
        db_handler = create_database_handler('mongodb', connection_string=conn_str, database_name=mongo_config['database'])
    else:
        logger.error(f"Unsupported database type: {db_type}")
        sys.exit(1)
    
    # Initialize HLR/HSS
    logger.info("Initializing HLR/HSS core...")
    hlr_hss = HLR_HSS(db_handler)

    ran_config = config.get('ran', {})
    enb_profiles = ran_config.get('enb_profiles', [])
    for profile_data in enb_profiles:
        try:
            profile = ENodeBProfile(**profile_data)
            hlr_hss.register_enb_profile(profile)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to load eNodeB profile {profile_data}: {e}")
    
    # Initialize sample data if requested
    if args.init_db:
        logger.info("Initializing database with sample data...")
        from hlr_hss.core import Subscriber
        
        sample_subscriber = Subscriber(
            imsi="001010000000001",
            msisdn="1234567890",
            ki="465B5CE8B199B49FAA5F0A2EE238A6BC",
            opc="E8ED289DEBA952E4283B54E88E6183CA",
            amf="8000",
            sqn=0,
            subscriber_status="SERVICE_GRANTED",
            roaming_allowed=True,
        )
        hlr_hss.create_subscriber(sample_subscriber)
        logger.info(f"Created sample subscriber: IMSI {sample_subscriber.imsi}")
    
    # Initialize OCS if enabled
    ocs = None
    ocs_config = config.get('ocs', {})
    if ocs_config.get('enabled', False):
        logger.info("Initializing Online Charging System (OCS)...")
        ocs = OnlineChargingSystem(db_handler)
    
    # Initialize Roaming Manager if enabled
    roaming_manager = None
    roaming_config = config.get('roaming', {})
    if roaming_config.get('enabled', False):
        network_config = config.get('network', {})
        plmn_id = network_config.get('plmn_id', '00101')
        logger.info("Initializing Roaming Manager...")
        roaming_manager = RoamingManager(plmn_id)
    
    # Initialize REST API if enabled
    api_config = config.get('api', {})
    if api_config.get('enabled', True):
        logger.info("Initializing REST API...")
        app = create_api(hlr_hss, ocs, roaming_manager)
        
        bind_address = api_config.get('bind_address', '0.0.0.0')
        port = api_config.get('port', 8080)
        debug = api_config.get('debug', False)
        
        logger.info(f"Starting REST API on {bind_address}:{port}")
        logger.info("="*60)
        logger.info("HLR/HSS is ready!")
        logger.info(f"API available at: http://{bind_address}:{port}")
        logger.info("="*60)
        
        app.run(host=bind_address, port=port, debug=debug)
    else:
        logger.info("="*60)
        logger.info("HLR/HSS is ready!")
        logger.info("="*60)
        
        # Keep running
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")


if __name__ == '__main__':
    main()
