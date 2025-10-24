"""
Database handlers for subscriber and location data
Supports: PostgreSQL, MySQL, MongoDB, Redis
"""
import logging
from typing import Dict, Optional, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DatabaseHandler(ABC):
    """Abstract base class for database handlers"""
    
    @abstractmethod
    def get_subscriber(self, imsi: str) -> Optional[Dict]:
        """Get subscriber by IMSI"""
        pass
    
    @abstractmethod
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Dict]:
        """Get subscriber by MSISDN"""
        pass
    
    @abstractmethod
    def create_subscriber(self, subscriber_data: Dict) -> bool:
        """Create new subscriber"""
        pass
    
    @abstractmethod
    def update_subscriber(self, imsi: str, updates: Dict) -> bool:
        """Update subscriber data"""
        pass
    
    @abstractmethod
    def delete_subscriber(self, imsi: str) -> bool:
        """Delete subscriber"""
        pass
    
    @abstractmethod
    def update_location(self, imsi: str, location_data: Dict) -> bool:
        """Update subscriber location"""
        pass
    
    @abstractmethod
    def get_location(self, imsi: str) -> Optional[Dict]:
        """Get subscriber location"""
        pass


class MemoryDatabase(DatabaseHandler):
    """
    In-memory database for testing and development
    """
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.subscribers = {}
        self.locations = {}
        self.msisdn_index = {}
        self.logger = logging.getLogger(__name__)
    
    def get_subscriber(self, imsi: str) -> Optional[Dict]:
        """Get subscriber by IMSI"""
        return self.subscribers.get(imsi)
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Dict]:
        """Get subscriber by MSISDN"""
        imsi = self.msisdn_index.get(msisdn)
        if imsi:
            return self.subscribers.get(imsi)
        return None
    
    def create_subscriber(self, subscriber_data: Dict) -> bool:
        """Create new subscriber"""
        try:
            imsi = subscriber_data.get('imsi')
            msisdn = subscriber_data.get('msisdn')
            
            if not imsi or not msisdn:
                return False
            
            if imsi in self.subscribers:
                self.logger.warning(f"Subscriber {imsi} already exists")
                return False
            
            self.subscribers[imsi] = subscriber_data
            self.msisdn_index[msisdn] = imsi
            return True
        except Exception as e:
            self.logger.error(f"Error creating subscriber: {e}")
            return False
    
    def update_subscriber(self, imsi: str, updates: Dict) -> bool:
        """Update subscriber data"""
        try:
            if imsi not in self.subscribers:
                return False
            
            # Update MSISDN index if changed
            old_msisdn = self.subscribers[imsi].get('msisdn')
            new_msisdn = updates.get('msisdn')
            
            if new_msisdn and new_msisdn != old_msisdn:
                if old_msisdn in self.msisdn_index:
                    del self.msisdn_index[old_msisdn]
                self.msisdn_index[new_msisdn] = imsi
            
            self.subscribers[imsi].update(updates)
            return True
        except Exception as e:
            self.logger.error(f"Error updating subscriber: {e}")
            return False
    
    def delete_subscriber(self, imsi: str) -> bool:
        """Delete subscriber"""
        try:
            if imsi not in self.subscribers:
                return False
            
            msisdn = self.subscribers[imsi].get('msisdn')
            if msisdn and msisdn in self.msisdn_index:
                del self.msisdn_index[msisdn]
            
            del self.subscribers[imsi]
            
            if imsi in self.locations:
                del self.locations[imsi]
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting subscriber: {e}")
            return False
    
    def update_location(self, imsi: str, location_data: Dict) -> bool:
        """Update subscriber location"""
        try:
            self.locations[imsi] = location_data
            return True
        except Exception as e:
            self.logger.error(f"Error updating location: {e}")
            return False
    
    def get_location(self, imsi: str) -> Optional[Dict]:
        """Get subscriber location"""
        return self.locations.get(imsi)
    
    def list_subscribers(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List subscribers with pagination"""
        subscribers = list(self.subscribers.values())
        return subscribers[offset:offset + limit]
    
    def count_subscribers(self) -> int:
        """Count total subscribers"""
        return len(self.subscribers)


class SQLDatabase(DatabaseHandler):
    """
    SQL database handler (PostgreSQL, MySQL)
    Using SQLAlchemy for database abstraction
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize SQL database connection
        
        Args:
            connection_string: Database connection URL
        """
        try:
            from sqlalchemy import create_engine, Table, Column, String, Integer, Boolean, MetaData, JSON
            from sqlalchemy.sql import select, insert, update, delete
            
            self.engine = create_engine(connection_string)
            self.metadata = MetaData()
            
            # Define subscribers table
            self.subscribers_table = Table(
                'subscribers',
                self.metadata,
                Column('imsi', String(15), primary_key=True),
                Column('msisdn', String(15), unique=True, index=True),
                Column('imei', String(15)),
                Column('ki', String(32)),
                Column('opc', String(32)),
                Column('op', String(32)),
                Column('amf', String(4)),
                Column('sqn', Integer),
                Column('apn_list', JSON),
                Column('default_apn', String(64)),
                Column('subscriber_status', String(32)),
                Column('roaming_allowed', Boolean),
                Column('serving_mme', String(64)),
                Column('qos_profile', JSON),
                Column('ambr_uplink', Integer),
                Column('ambr_downlink', Integer),
            )
            
            # Define locations table
            self.locations_table = Table(
                'locations',
                self.metadata,
                Column('imsi', String(15), primary_key=True),
                Column('location_area', String(10)),
                Column('routing_area', String(10)),
                Column('tracking_area', String(10)),
                Column('cell_id', String(16)),
                Column('serving_node', String(64)),
            )
            
            # Create tables if not exist
            self.metadata.create_all(self.engine)
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("SQL database initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing SQL database: {e}")
            raise
    
    def get_subscriber(self, imsi: str) -> Optional[Dict]:
        """Get subscriber by IMSI"""
        try:
            from sqlalchemy.sql import select
            
            with self.engine.connect() as conn:
                stmt = select(self.subscribers_table).where(
                    self.subscribers_table.c.imsi == imsi
                )
                result = conn.execute(stmt).fetchone()
                if result:
                    return dict(result._mapping)
                return None
        except Exception as e:
            self.logger.error(f"Error getting subscriber: {e}")
            return None
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Dict]:
        """Get subscriber by MSISDN"""
        try:
            from sqlalchemy.sql import select
            
            with self.engine.connect() as conn:
                stmt = select(self.subscribers_table).where(
                    self.subscribers_table.c.msisdn == msisdn
                )
                result = conn.execute(stmt).fetchone()
                if result:
                    return dict(result._mapping)
                return None
        except Exception as e:
            self.logger.error(f"Error getting subscriber by MSISDN: {e}")
            return None
    
    def create_subscriber(self, subscriber_data: Dict) -> bool:
        """Create new subscriber"""
        try:
            from sqlalchemy.sql import insert
            
            with self.engine.connect() as conn:
                stmt = insert(self.subscribers_table).values(**subscriber_data)
                conn.execute(stmt)
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error creating subscriber: {e}")
            return False
    
    def update_subscriber(self, imsi: str, updates: Dict) -> bool:
        """Update subscriber data"""
        try:
            from sqlalchemy.sql import update as sql_update
            
            with self.engine.connect() as conn:
                stmt = sql_update(self.subscribers_table).where(
                    self.subscribers_table.c.imsi == imsi
                ).values(**updates)
                conn.execute(stmt)
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error updating subscriber: {e}")
            return False
    
    def delete_subscriber(self, imsi: str) -> bool:
        """Delete subscriber"""
        try:
            from sqlalchemy.sql import delete as sql_delete
            
            with self.engine.connect() as conn:
                stmt = sql_delete(self.subscribers_table).where(
                    self.subscribers_table.c.imsi == imsi
                )
                conn.execute(stmt)
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error deleting subscriber: {e}")
            return False
    
    def update_location(self, imsi: str, location_data: Dict) -> bool:
        """Update subscriber location"""
        try:
            from sqlalchemy.dialects.postgresql import insert
            from sqlalchemy.sql import update as sql_update
            
            with self.engine.connect() as conn:
                # Try insert first, if exists then update
                stmt = insert(self.locations_table).values(
                    imsi=imsi, **location_data
                ).on_conflict_do_update(
                    index_elements=['imsi'],
                    set_=location_data
                )
                conn.execute(stmt)
                conn.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error updating location: {e}")
            return False
    
    def get_location(self, imsi: str) -> Optional[Dict]:
        """Get subscriber location"""
        try:
            from sqlalchemy.sql import select
            
            with self.engine.connect() as conn:
                stmt = select(self.locations_table).where(
                    self.locations_table.c.imsi == imsi
                )
                result = conn.execute(stmt).fetchone()
                if result:
                    return dict(result._mapping)
                return None
        except Exception as e:
            self.logger.error(f"Error getting location: {e}")
            return None


class MongoDatabase(DatabaseHandler):
    """
    MongoDB database handler
    """
    
    def __init__(self, connection_string: str, database_name: str = "hlr_hss"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection URL
            database_name: Database name
        """
        try:
            from pymongo import MongoClient
            
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            self.subscribers = self.db['subscribers']
            self.locations = self.db['locations']
            
            # Create indexes
            self.subscribers.create_index('imsi', unique=True)
            self.subscribers.create_index('msisdn', unique=True)
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("MongoDB database initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing MongoDB: {e}")
            raise
    
    def get_subscriber(self, imsi: str) -> Optional[Dict]:
        """Get subscriber by IMSI"""
        try:
            result = self.subscribers.find_one({'imsi': imsi})
            if result:
                result.pop('_id', None)
            return result
        except Exception as e:
            self.logger.error(f"Error getting subscriber: {e}")
            return None
    
    def get_subscriber_by_msisdn(self, msisdn: str) -> Optional[Dict]:
        """Get subscriber by MSISDN"""
        try:
            result = self.subscribers.find_one({'msisdn': msisdn})
            if result:
                result.pop('_id', None)
            return result
        except Exception as e:
            self.logger.error(f"Error getting subscriber by MSISDN: {e}")
            return None
    
    def create_subscriber(self, subscriber_data: Dict) -> bool:
        """Create new subscriber"""
        try:
            self.subscribers.insert_one(subscriber_data)
            return True
        except Exception as e:
            self.logger.error(f"Error creating subscriber: {e}")
            return False
    
    def update_subscriber(self, imsi: str, updates: Dict) -> bool:
        """Update subscriber data"""
        try:
            result = self.subscribers.update_one(
                {'imsi': imsi},
                {'$set': updates}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Error updating subscriber: {e}")
            return False
    
    def delete_subscriber(self, imsi: str) -> bool:
        """Delete subscriber"""
        try:
            result = self.subscribers.delete_one({'imsi': imsi})
            self.locations.delete_one({'imsi': imsi})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Error deleting subscriber: {e}")
            return False
    
    def update_location(self, imsi: str, location_data: Dict) -> bool:
        """Update subscriber location"""
        try:
            self.locations.update_one(
                {'imsi': imsi},
                {'$set': location_data},
                upsert=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Error updating location: {e}")
            return False
    
    def get_location(self, imsi: str) -> Optional[Dict]:
        """Get subscriber location"""
        try:
            result = self.locations.find_one({'imsi': imsi})
            if result:
                result.pop('_id', None)
            return result
        except Exception as e:
            self.logger.error(f"Error getting location: {e}")
            return None


def create_database_handler(db_type: str, **kwargs) -> DatabaseHandler:
    """
    Factory function to create appropriate database handler
    
    Args:
        db_type: Type of database ('memory', 'postgresql', 'mysql', 'mongodb')
        **kwargs: Database connection parameters
        
    Returns:
        DatabaseHandler instance
    """
    if db_type == 'memory':
        return MemoryDatabase()
    elif db_type in ['postgresql', 'mysql']:
        connection_string = kwargs.get('connection_string')
        if not connection_string:
            raise ValueError("connection_string required for SQL databases")
        return SQLDatabase(connection_string)
    elif db_type == 'mongodb':
        connection_string = kwargs.get('connection_string')
        database_name = kwargs.get('database_name', 'hlr_hss')
        if not connection_string:
            raise ValueError("connection_string required for MongoDB")
        return MongoDatabase(connection_string, database_name)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
