"""
Example: Roaming configuration
"""
from hlr_hss.roaming import RoamingManager, RoamingPartner, RoamingPolicy, RoamingType


def main():
    """Example of roaming configuration and management"""
    
    print("=" * 60)
    print("Roaming Management Example")
    print("=" * 60)
    
    # Create roaming manager for home network
    home_plmn = "00101"  # MCC=001, MNC=01
    roaming_mgr = RoamingManager(home_plmn)
    
    # Add roaming partners
    print("\n1. Adding roaming partners...")
    
    # National roaming partner
    partner1 = RoamingPartner(
        partner_id="partner_001",
        partner_name="National Operator A",
        plmn_id="00102",
        country_code="US",
        roaming_type=RoamingType.NATIONAL,
        agreement_active=True,
        data_rate=0.02,
        voice_rate=0.15,
        sms_rate=0.07,
        s6a_peers=["hss.partner-a.local"],
        diameter_realm="partner-a.local"
    )
    roaming_mgr.add_partner(partner1)
    print(f"   Added partner: {partner1.partner_name}")
    
    # International roaming partner
    partner2 = RoamingPartner(
        partner_id="partner_002",
        partner_name="International Operator B",
        plmn_id="23001",
        country_code="CZ",
        roaming_type=RoamingType.INTERNATIONAL,
        agreement_active=True,
        data_rate=0.10,
        voice_rate=0.50,
        sms_rate=0.20,
        s6a_peers=["hss.partner-b.int"],
        diameter_realm="partner-b.int"
    )
    roaming_mgr.add_partner(partner2)
    print(f"   Added partner: {partner2.partner_name}")
    
    # Create roaming policies
    print("\n2. Creating roaming policies...")
    
    # Policy for premium subscribers
    premium_policy = RoamingPolicy(
        policy_id="premium",
        name="Premium Roaming",
        national_roaming=True,
        international_roaming=True,
        data_roaming=True,
        voice_roaming=True,
        sms_roaming=True,
        daily_data_limit_mb=1000,
        monthly_data_limit_mb=10000
    )
    roaming_mgr.add_policy(premium_policy)
    print(f"   Added policy: {premium_policy.name}")
    
    # Policy for standard subscribers
    standard_policy = RoamingPolicy(
        policy_id="standard",
        name="Standard Roaming",
        national_roaming=True,
        international_roaming=False,
        data_roaming=True,
        voice_roaming=True,
        sms_roaming=True,
        daily_data_limit_mb=100,
        monthly_data_limit_mb=3000
    )
    roaming_mgr.add_policy(standard_policy)
    print(f"   Added policy: {standard_policy.name}")
    
    # Check roaming permissions
    print("\n3. Checking roaming permissions...")
    
    subscriber_imsi = "001010000000001"
    
    # Check national roaming
    allowed, reason = roaming_mgr.check_roaming_allowed(
        subscriber_imsi, "00102", policy_id="standard"
    )
    print(f"   National roaming: {allowed} - {reason}")
    
    # Check international roaming
    allowed, reason = roaming_mgr.check_roaming_allowed(
        subscriber_imsi, "23001", policy_id="standard"
    )
    print(f"   International roaming (standard): {allowed} - {reason}")
    
    allowed, reason = roaming_mgr.check_roaming_allowed(
        subscriber_imsi, "23001", policy_id="premium"
    )
    print(f"   International roaming (premium): {allowed} - {reason}")
    
    # Get roaming rates
    print("\n4. Getting roaming rates...")
    rates = roaming_mgr.get_roaming_rates("00102")
    if rates:
        print(f"   National partner rates:")
        print(f"   - Data: ${rates['data_rate']:.2f}/MB")
        print(f"   - Voice: ${rates['voice_rate']:.2f}/min")
        print(f"   - SMS: ${rates['sms_rate']:.2f}/msg")
    
    rates = roaming_mgr.get_roaming_rates("23001")
    if rates:
        print(f"\n   International partner rates:")
        print(f"   - Data: ${rates['data_rate']:.2f}/MB")
        print(f"   - Voice: ${rates['voice_rate']:.2f}/min")
        print(f"   - SMS: ${rates['sms_rate']:.2f}/msg")
    
    # List all partners
    print("\n5. Listing roaming partners...")
    partners = roaming_mgr.list_partners()
    for partner in partners:
        print(f"   - {partner.partner_name} ({partner.plmn_id}) - {partner.roaming_type.value}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
