"""
Example: Basic subscriber management
"""
from hlr_hss.core import HLR_HSS, Subscriber
from hlr_hss.database import create_database_handler


def main():
    """Example of basic subscriber operations"""
    
    # Create database handler (in-memory for this example)
    db = create_database_handler('memory')
    
    # Create HLR/HSS instance
    hlr_hss = HLR_HSS(db)
    
    print("=" * 60)
    print("HLR/HSS Subscriber Management Example")
    print("=" * 60)
    
    # Create a new subscriber
    print("\n1. Creating new subscriber...")
    subscriber = Subscriber(
        imsi="001010000000001",
        msisdn="1234567890",
        ki="465B5CE8B199B49FAA5F0A2EE238A6BC",
        opc="E8ED289DEBA952E4283B54E88E6183CA",
        amf="8000",
        sqn=0,
        subscriber_status="SERVICE_GRANTED",
        roaming_allowed=True,
    )
    
    success = hlr_hss.create_subscriber(subscriber)
    print(f"   Subscriber created: {success}")
    print(f"   IMSI: {subscriber.imsi}")
    print(f"   MSISDN: {subscriber.msisdn}")
    
    # Retrieve subscriber
    print("\n2. Retrieving subscriber...")
    retrieved = hlr_hss.get_subscriber(subscriber.imsi)
    if retrieved:
        print(f"   Found subscriber: {retrieved.imsi}")
        print(f"   Status: {retrieved.subscriber_status}")
        print(f"   Roaming allowed: {retrieved.roaming_allowed}")
    
    # Update subscriber
    print("\n3. Updating subscriber...")
    updates = {
        'serving_mme': 'mme.opennetwork.local',
        'sqn': 5
    }
    success = hlr_hss.update_subscriber(subscriber.imsi, updates)
    print(f"   Subscriber updated: {success}")
    
    # Verify update
    retrieved = hlr_hss.get_subscriber(subscriber.imsi)
    print(f"   Serving MME: {retrieved.serving_mme}")
    print(f"   SQN: {retrieved.sqn}")
    
    # Check if subscriber is active
    print("\n4. Checking subscriber status...")
    is_active = hlr_hss.is_subscriber_active(subscriber.imsi)
    print(f"   Subscriber active: {is_active}")
    
    # Update location
    print("\n5. Updating location...")
    from hlr_hss.core import LocationInfo
    from datetime import datetime
    
    location = LocationInfo(
        imsi=subscriber.imsi,
        tracking_area="TAC001",
        cell_id="CELL12345",
        serving_node="mme.opennetwork.local",
        last_update=datetime.now()
    )
    
    success = hlr_hss.update_location(location)
    print(f"   Location updated: {success}")
    
    # Retrieve location
    retrieved_location = hlr_hss.get_location(subscriber.imsi)
    if retrieved_location:
        print(f"   Tracking Area: {retrieved_location.tracking_area}")
        print(f"   Cell ID: {retrieved_location.cell_id}")
        print(f"   Serving Node: {retrieved_location.serving_node}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
