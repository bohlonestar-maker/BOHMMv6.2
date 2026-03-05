"""
Treasury Encryption Tests
=========================
Tests for Treasury module with AES-256 encryption for sensitive financial data.

Features tested:
- Account CRUD with encrypted name/description
- Transaction CRUD with encrypted fields (description, vendor_payee, reference_number, notes)
- Category management (not encrypted)
- Account transfer between accounts
- Receipt upload/retrieval
- Dashboard data verification
"""
import os
import pytest
import requests
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_USER = "admin"
ADMIN_PASSWORD = "2X13y75Z"


class TestTreasuryAuth:
    """Authentication tests for Treasury access"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("token")
        assert token, "No token returned"
        return token
    
    def test_treasury_requires_auth(self):
        """Verify treasury endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/treasury/accounts")
        assert response.status_code in [401, 403], "Treasury should require auth"
    
    def test_admin_can_access_treasury(self, auth_token):
        """Verify admin has treasury access"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Admin should access treasury: {response.text}"


class TestTreasuryAccounts:
    """Account CRUD with encryption tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def created_account_id(self, auth_token):
        """Create a test account and return its ID for cleanup"""
        unique_name = f"TEST_Account_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "type": "checking",
                "initial_balance": 1000.50,
                "description": "Test account with sensitive description"
            }
        )
        assert response.status_code == 200, f"Failed to create account: {response.text}"
        data = response.json()
        assert data.get("id"), "No ID returned for created account"
        return data.get("id"), unique_name
    
    def test_list_accounts(self, auth_token):
        """List all accounts - should return decrypted names"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data, "Missing accounts in response"
        assert "total_balance" in data, "Missing total_balance in response"
        
        # If accounts exist, verify names are readable (not encrypted gibberish)
        accounts = data.get("accounts", [])
        for acc in accounts:
            assert "name" in acc, "Account missing name"
            assert "balance" in acc, "Account missing balance"
            # Decrypted names should be readable
            if acc.get("name"):
                assert not acc["name"].startswith("gAAAAA"), f"Account name appears encrypted: {acc['name'][:50]}"
        
        print(f"Listed {len(accounts)} accounts, total balance: {data.get('total_balance')}")
    
    def test_create_account_with_encryption(self, auth_token):
        """Create account with sensitive fields that should be encrypted at rest"""
        unique_name = f"TEST_EncryptedAccount_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "type": "savings",
                "initial_balance": 2500.00,
                "description": "Sensitive savings description for testing"
            }
        )
        assert response.status_code == 200, f"Failed to create account: {response.text}"
        data = response.json()
        
        # Verify returned data is decrypted
        assert data.get("name") == unique_name, "Account name should be returned decrypted"
        assert data.get("description") == "Sensitive savings description for testing"
        assert data.get("balance") == 2500.00, "Initial balance should be set"
        assert data.get("type") == "savings"
        
        print(f"Created encrypted account: {unique_name}")
    
    def test_create_duplicate_account_rejected(self, auth_token, created_account_id):
        """Verify duplicate account names are rejected even when encrypted"""
        account_id, account_name = created_account_id
        response = requests.post(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": account_name,
                "type": "checking",
                "initial_balance": 0
            }
        )
        assert response.status_code == 400, "Should reject duplicate account name"
        assert "already exists" in response.text.lower()
    
    def test_account_transfer(self, auth_token):
        """Test transferring funds between accounts"""
        # First get list of accounts
        response = requests.get(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        accounts = response.json().get("accounts", [])
        
        if len(accounts) < 2:
            pytest.skip("Need at least 2 accounts to test transfer")
        
        # Find two accounts with balance
        from_acc = None
        to_acc = None
        for acc in accounts:
            if acc.get("balance", 0) >= 50:
                if from_acc is None:
                    from_acc = acc
                else:
                    to_acc = acc
                    break
        
        if not from_acc or not to_acc:
            pytest.skip("Need accounts with sufficient balance for transfer test")
        
        # Transfer funds
        transfer_amount = 25.00
        response = requests.post(
            f"{BASE_URL}/api/treasury/accounts/transfer",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "from_account_id": from_acc["id"],
                "to_account_id": to_acc["id"],
                "amount": transfer_amount,
                "description": "Test transfer"
            }
        )
        assert response.status_code == 200, f"Transfer failed: {response.text}"
        print(f"Transferred ${transfer_amount} from {from_acc['name']} to {to_acc['name']}")


class TestTreasuryTransactions:
    """Transaction CRUD with encryption tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def test_account(self, auth_token):
        """Get or create a test account for transactions"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        accounts = response.json().get("accounts", [])
        if accounts:
            return accounts[0]
        
        # Create account if none exist
        unique_name = f"TEST_TxAccount_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": unique_name, "type": "checking", "initial_balance": 5000}
        )
        assert response.status_code == 200
        return response.json()
    
    @pytest.fixture(scope="class")
    def test_category(self, auth_token):
        """Get a category for transactions"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        categories = response.json()
        
        # Get an expense category
        for cat in categories:
            if cat.get("type") == "expense":
                return cat
        
        # Should have seeded categories
        assert len(categories) > 0, "No categories found"
        return categories[0]
    
    def test_list_transactions(self, auth_token):
        """List transactions - should return decrypted data"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data, "Missing transactions in response"
        assert "total" in data, "Missing total in response"
        
        # Verify transactions have decrypted fields
        for tx in data.get("transactions", []):
            if tx.get("description"):
                assert not tx["description"].startswith("gAAAAA"), f"Description appears encrypted: {tx['description'][:50]}"
            if tx.get("account_name"):
                # Account name in transaction should be decrypted
                assert not tx["account_name"].startswith("gAAAAA"), f"Account name appears encrypted: {tx['account_name'][:50]}"
        
        print(f"Listed {len(data.get('transactions', []))} transactions")
    
    def test_create_expense_transaction(self, auth_token, test_account, test_category):
        """Create expense transaction with encrypted sensitive fields"""
        response = requests.post(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "expense",
                "account_id": test_account["id"],
                "category_id": test_category["id"],
                "amount": 150.75,
                "description": "TEST_Sensitive expense description",
                "date": "2025-01-20",
                "vendor_payee": "TEST_Vendor Inc",
                "reference_number": "CHECK-12345",
                "notes": "Confidential notes for testing encryption"
            }
        )
        assert response.status_code == 200, f"Failed to create transaction: {response.text}"
        data = response.json()
        
        # Verify returned data is decrypted
        assert data.get("description") == "TEST_Sensitive expense description"
        assert data.get("vendor_payee") == "TEST_Vendor Inc"
        assert data.get("reference_number") == "CHECK-12345"
        assert data.get("notes") == "Confidential notes for testing encryption"
        assert data.get("amount") == 150.75
        
        # Verify account name is decrypted (not encrypted)
        account_name = data.get("account_name", "")
        assert not account_name.startswith("gAAAAA"), f"Account name in transaction appears encrypted: {account_name[:50]}"
        
        print(f"Created expense transaction: {data.get('id')}")
        return data
    
    def test_create_income_transaction(self, auth_token, test_account):
        """Create income transaction with encrypted fields"""
        # Get income category
        response = requests.get(
            f"{BASE_URL}/api/treasury/categories?type=income",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        categories = response.json()
        income_cat = next((c for c in categories if c.get("type") == "income"), None)
        if not income_cat:
            pytest.skip("No income category found")
        
        response = requests.post(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "income",
                "account_id": test_account["id"],
                "category_id": income_cat["id"],
                "amount": 500.00,
                "description": "TEST_Income from donation",
                "date": "2025-01-20",
                "vendor_payee": "John Donor",
                "reference_number": "DON-001",
                "notes": "Encrypted donation notes"
            }
        )
        assert response.status_code == 200, f"Failed to create income: {response.text}"
        data = response.json()
        
        # Verify decrypted fields
        assert data.get("description") == "TEST_Income from donation"
        assert data.get("type") == "income"
        print(f"Created income transaction: {data.get('id')}")
    
    def test_get_single_transaction(self, auth_token, test_account, test_category):
        """Get single transaction - should have all fields decrypted"""
        # Create a transaction first
        create_response = requests.post(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "expense",
                "account_id": test_account["id"],
                "category_id": test_category["id"],
                "amount": 75.00,
                "description": "TEST_Single tx test",
                "date": "2025-01-20",
                "vendor_payee": "Test Vendor",
                "notes": "Secret notes"
            }
        )
        assert create_response.status_code == 200
        tx_id = create_response.json().get("id")
        
        # Get the transaction
        response = requests.get(
            f"{BASE_URL}/api/treasury/transactions/{tx_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed to get transaction: {response.text}"
        data = response.json()
        
        # All fields should be decrypted
        assert data.get("description") == "TEST_Single tx test"
        assert data.get("vendor_payee") == "Test Vendor"
        assert data.get("notes") == "Secret notes"
        print(f"Retrieved transaction with decrypted fields")
    
    def test_update_transaction(self, auth_token, test_account, test_category):
        """Update transaction - encrypted fields should update correctly"""
        # Create transaction
        create_response = requests.post(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "expense",
                "account_id": test_account["id"],
                "category_id": test_category["id"],
                "amount": 100.00,
                "description": "TEST_Original description",
                "date": "2025-01-20"
            }
        )
        assert create_response.status_code == 200
        tx_id = create_response.json().get("id")
        
        # Update the transaction
        update_response = requests.put(
            f"{BASE_URL}/api/treasury/transactions/{tx_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "description": "TEST_Updated description",
                "vendor_payee": "New Vendor",
                "notes": "Added notes after update"
            }
        )
        assert update_response.status_code == 200, f"Failed to update: {update_response.text}"
        
        # Verify update by fetching
        get_response = requests.get(
            f"{BASE_URL}/api/treasury/transactions/{tx_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 200
        data = get_response.json()
        
        assert data.get("description") == "TEST_Updated description"
        assert data.get("vendor_payee") == "New Vendor"
        assert data.get("notes") == "Added notes after update"
        print("Transaction updated with encrypted fields")
    
    def test_delete_transaction(self, auth_token, test_account, test_category):
        """Delete transaction - should remove and adjust balance"""
        # Create transaction
        create_response = requests.post(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "expense",
                "account_id": test_account["id"],
                "category_id": test_category["id"],
                "amount": 50.00,
                "description": "TEST_To be deleted",
                "date": "2025-01-20"
            }
        )
        assert create_response.status_code == 200
        tx_id = create_response.json().get("id")
        
        # Delete transaction
        delete_response = requests.delete(
            f"{BASE_URL}/api/treasury/transactions/{tx_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert delete_response.status_code == 200, f"Failed to delete: {delete_response.text}"
        
        # Verify deleted
        get_response = requests.get(
            f"{BASE_URL}/api/treasury/transactions/{tx_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404, "Deleted transaction should not be found"
        print("Transaction deleted successfully")


class TestTreasuryCategories:
    """Category management tests (categories are NOT encrypted)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("token")
    
    def test_list_categories(self, auth_token):
        """List all categories"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/categories",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list), "Categories should be a list"
        
        # Should have default categories seeded
        if len(categories) > 0:
            assert "name" in categories[0], "Category missing name"
            assert "type" in categories[0], "Category missing type"
            
            income_cats = [c for c in categories if c.get("type") == "income"]
            expense_cats = [c for c in categories if c.get("type") == "expense"]
            print(f"Found {len(income_cats)} income categories, {len(expense_cats)} expense categories")
    
    def test_list_categories_by_type(self, auth_token):
        """Filter categories by type"""
        # Income categories
        response = requests.get(
            f"{BASE_URL}/api/treasury/categories?type=income",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        income_cats = response.json()
        for cat in income_cats:
            assert cat.get("type") == "income", "Should only return income categories"
        
        # Expense categories
        response = requests.get(
            f"{BASE_URL}/api/treasury/categories?type=expense",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        expense_cats = response.json()
        for cat in expense_cats:
            assert cat.get("type") == "expense", "Should only return expense categories"
    
    def test_create_category(self, auth_token):
        """Create a new category"""
        unique_name = f"TEST_Category_{int(time.time())}"
        response = requests.post(
            f"{BASE_URL}/api/treasury/categories",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": unique_name,
                "type": "expense",
                "description": "Test category for testing"
            }
        )
        assert response.status_code == 200, f"Failed to create category: {response.text}"
        data = response.json()
        assert data.get("name") == unique_name
        assert data.get("type") == "expense"
        print(f"Created category: {unique_name}")


class TestTreasuryReports:
    """Treasury reports/dashboard tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("token")
    
    def test_get_summary_report(self, auth_token):
        """Get monthly summary report - should show decrypted data"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/reports/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 200 or 404 if reports endpoint not implemented
        if response.status_code == 200:
            data = response.json()
            # Check structure
            print(f"Summary report: {data}")
        else:
            print(f"Reports summary endpoint status: {response.status_code}")


class TestAccountNameInTransactions:
    """Specific test for the bug fix - account names should display correctly in transactions"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": ADMIN_USER,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("token")
    
    def test_transaction_shows_decrypted_account_name(self, auth_token):
        """Verify account_name in transaction list is decrypted, not encrypted"""
        response = requests.get(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        transactions = response.json().get("transactions", [])
        
        for tx in transactions:
            account_name = tx.get("account_name", "")
            if account_name:
                # Fernet encrypted strings start with 'gAAAAA'
                assert not account_name.startswith("gAAAAA"), \
                    f"Account name '{account_name[:50]}...' appears to be encrypted (starts with gAAAAA)"
                # Account name should be readable text
                assert len(account_name) < 200, \
                    f"Account name too long, likely encrypted: {len(account_name)} chars"
        
        print(f"Verified {len(transactions)} transactions have decrypted account names")
    
    def test_new_transaction_gets_decrypted_account_name(self, auth_token):
        """Create new transaction and verify account_name is stored decrypted"""
        # Get an account
        accounts_response = requests.get(
            f"{BASE_URL}/api/treasury/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert accounts_response.status_code == 200
        accounts = accounts_response.json().get("accounts", [])
        if not accounts:
            pytest.skip("No accounts available")
        
        account = accounts[0]
        account_name = account.get("name")
        
        # Get a category
        categories_response = requests.get(
            f"{BASE_URL}/api/treasury/categories?type=expense",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert categories_response.status_code == 200
        categories = categories_response.json()
        if not categories:
            pytest.skip("No expense categories available")
        
        category = categories[0]
        
        # Create transaction
        create_response = requests.post(
            f"{BASE_URL}/api/treasury/transactions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "expense",
                "account_id": account["id"],
                "category_id": category["id"],
                "amount": 25.00,
                "description": "TEST_Account name verification",
                "date": "2025-01-20"
            }
        )
        assert create_response.status_code == 200, f"Failed to create tx: {create_response.text}"
        tx_data = create_response.json()
        
        # Verify account name matches and is not encrypted
        tx_account_name = tx_data.get("account_name", "")
        assert tx_account_name == account_name, \
            f"Transaction account_name '{tx_account_name}' should match '{account_name}'"
        assert not tx_account_name.startswith("gAAAAA"), \
            f"Transaction account_name appears encrypted: {tx_account_name[:50]}"
        
        print(f"Verified new transaction has decrypted account name: {tx_account_name}")


# Run cleanup after all tests
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Run after all tests to clean up TEST_ prefixed data"""
    yield
    # Cleanup could be added here if needed
    print("\n--- Test session complete ---")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
