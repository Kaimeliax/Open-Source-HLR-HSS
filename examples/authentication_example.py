"""
Example: Authentication vector generation
"""
from hlr_hss.authentication import AuthenticationManager


def main():
    """Example of authentication vector generation"""
    
    print("=" * 60)
    print("Authentication Vector Generation Example")
    print("=" * 60)
    
    # Create authentication manager
    auth_mgr = AuthenticationManager()
    
    # Subscriber credentials
    k = "465B5CE8B199B49FAA5F0A2EE238A6BC"
    opc = "E8ED289DEBA952E4283B54E88E6183CA"
    amf = "8000"
    sqn = 0
    
    # Generate authentication vector using Milenage
    print("\n1. Generating authentication vector using Milenage...")
    auth_vec = auth_mgr.generate_auth_vector('milenage', k, opc, amf, sqn)
    
    if auth_vec:
        print("   Authentication vector generated successfully!")
        print(f"   RAND:  {auth_vec['rand']}")
        print(f"   AUTN:  {auth_vec['autn']}")
        print(f"   XRES:  {auth_vec['xres']}")
        print(f"   KASME: {auth_vec['kasme']}")
        print(f"   CK:    {auth_vec['ck']}")
        print(f"   IK:    {auth_vec['ik']}")
    else:
        print("   Failed to generate authentication vector")
    
    # Generate using XOR algorithm (for testing)
    print("\n2. Generating authentication vector using XOR...")
    auth_vec_xor = auth_mgr.generate_auth_vector('xor', k, None, amf, sqn)
    
    if auth_vec_xor:
        print("   Authentication vector generated successfully!")
        print(f"   RAND:  {auth_vec_xor['rand']}")
        print(f"   AUTN:  {auth_vec_xor['autn']}")
        print(f"   XRES:  {auth_vec_xor['xres']}")
    
    # Verify response
    print("\n3. Verifying authentication response...")
    xres = auth_vec['xres']
    res = auth_vec['xres']  # Simulating correct response
    
    is_valid = auth_mgr.verify_response(xres, res)
    print(f"   Response verification: {is_valid}")
    
    # Test incorrect response
    wrong_res = "0000000000000000"
    is_valid = auth_mgr.verify_response(xres, wrong_res)
    print(f"   Wrong response verification: {is_valid}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
