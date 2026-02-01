import os
from seisclass import check_seed


def test_check_seed():
    """Test check_seed function"""
    # Get test data path
    test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'seisclass', 'resource')
    test_seed = os.path.join(test_data_dir, 'test.seed')
    test_phase = os.path.join(test_data_dir, 'test.phase')
    
    # Simulate actual user usage
    print("\n=== Testing seisclass library usage ===")
    print(f"SEED file used: {test_seed}")
    print(f"Phase file used: {test_phase}")
    
    try:
        # Call function (consistent with user code)
        result = check_seed(test_seed, test_phase)
        
        # Output result
        print(f"\n=== Test result ===")
        print(f"Classification result: {result}")
        print("Test successful!")
        
    except Exception as e:
        print(f"\nTest failed: {e}")


if __name__ == "__main__":
    """Simulate user usage scenario when running directly"""
    test_check_seed()