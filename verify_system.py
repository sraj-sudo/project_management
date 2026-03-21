import sys
import os
import sqlite3
import json
from unittest.mock import MagicMock

# Mock Streamlit
mock_st = MagicMock()
mock_st.session_state = {}
sys.modules["streamlit"] = mock_st

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.db import init_db, add_issue, update_issue_status, get_issues, get_issue_details, create_user, get_user_by_username
from utils.auth import authenticate, verify_password

def test_db_init_and_seeding():
    print("Testing DB initialization and Safe Admin Seeding...")
    init_db()
    db_path = os.path.join('data', 'issues.db')
    assert os.path.exists(db_path)
    
    user = get_user_by_username("admin")
    assert user is not None
    assert user['role'] == 'admin'
    
    # Try seeding again (should not duplicate or error)
    init_db()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM users WHERE username = 'admin'")
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()
    print("✅ Safe Seeding Successful")

def test_bcrypt_auth():
    print("Testing Bcrypt Authentication...")
    # Admin was seeded with 'admin123'
    admin = authenticate("admin", "admin123")
    assert admin is not None
    assert admin['role'] == 'admin'
    
    invalid = authenticate("admin", "wrong")
    assert invalid is None
    print("✅ Bcrypt Auth Successful")

def test_role_enforcement():
    print("Testing Backend Role Enforcement...")
    
    # Create a Developer
    create_user("dev1", "dev123", "developer", "admin")
    dev = get_user_by_username("dev1")
    assert dev is not None
    
    # Create an issue
    issue_data = {
        'title': 'Auth Test Bug',
        'description': 'Description',
        'type': 'Bug',
        'priority': 'P0',
        'reporter': 'admin'
    }
    issue_id = add_issue(issue_data)
    
    # 1. Reporter should NOT be able to update status
    print("Testing Unauthorized Reporter Update...")
    try:
        update_issue_status(issue_id, "In Progress", "some_reporter", "reporter")
        assert False, "Reporter should not be allowed to update status"
    except Exception as e:
        print(f"Caught expected error: {e}")
        assert "Unauthorized" in str(e)
    
    # 2. Developer should NOT be able to update UNASSIGNED issue
    print("Testing Developer Unassigned Update...")
    try:
        update_issue_status(issue_id, "In Progress", "dev1", "developer")
        assert False, "Developer should not be allowed to update unassigned issue"
    except Exception as e:
        print(f"Caught expected error: {e}")
        assert "assigned" in str(e).lower()
        
    # 3. Admin assigns to Developer
    from utils.db import assign_issue
    assign_issue(issue_id, "dev1", "admin")
    
    # 4. Developer updates ASSIGNED issue
    print("Testing Developer Assigned Update...")
    update_issue_status(issue_id, "In Progress", "dev1", "developer")
    details = get_issue_details(issue_id)
    assert details['status'] == 'In Progress'
    
    # 5. Developer tries invalid transition (In Progress -> Closed directly depends on your rule, 
    # but let's test a generic invalid one if any)
    # New rule: In Progress -> Testing
    print("Testing Developer Invalid Transition...")
    try:
        update_issue_status(issue_id, "Closed", "dev1", "developer")
        assert False, "Developer should not be allowed invalid transition"
    except Exception as e:
        print(f"Caught expected error: {e}")
        assert "transition" in str(e)

    print("✅ Role Enforcement Successful")

if __name__ == "__main__":
    try:
        # Clean up existing test DB if any
        if os.path.exists('data/issues.db'):
            os.remove('data/issues.db')
        os.makedirs('data', exist_ok=True)
            
        test_db_init_and_seeding()
        test_bcrypt_auth()
        test_role_enforcement()
        print("\nALL PRODUCTION-GRADE TESTS PASSED!")
    except Exception as e:
        print(f"\nTESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
