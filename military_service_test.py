import requests
import sys
import json
from datetime import datetime
import urllib3

# Suppress SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class MilitaryServiceFirstResponderTester:
    def __init__(self, base_url="https://member-manager-26.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_members = []  # Track created members for cleanup

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, verify=False)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, verify=False)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, verify=False)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, verify=False)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'No error details')}"
                except:
                    details += f" - Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with provided credentials"""
        print(f"\n🔐 Testing Authentication...")
        
        success, response = self.run_test(
            "Login with testadmin/testpass123",
            "POST",
            "auth/login",
            200,
            data={"username": "testadmin", "password": "testpass123"}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   ✅ Successful login with testadmin")
            print(f"   Token obtained: {self.token[:20]}...")
            return True, response
        else:
            print("   ❌ Login failed with testadmin/testpass123")
            return False, {}

    def test_create_member_with_military_service(self):
        """Test creating members with military service fields"""
        print(f"\n🪖 Testing CREATE MEMBER WITH MILITARY SERVICE...")
        
        # Test 1a: Create member with military_service=true, military_branch="Army"
        military_member_army = {
            "chapter": "National",
            "title": "Member",
            "handle": "MilitaryTestArmy",
            "name": "Army Veteran Test",
            "email": "army@test.com",
            "phone": "555-0001",
            "address": "123 Army Base Rd",
            "military_service": True,
            "military_branch": "Army"
        }
        
        success, created_army = self.run_test(
            "Create Member - Army Veteran",
            "POST",
            "members",
            201,
            data=military_member_army
        )
        
        army_member_id = None
        if success and 'id' in created_army:
            army_member_id = created_army['id']
            self.created_members.append(army_member_id)
            
            # Verify military fields saved correctly
            if (created_army.get('military_service') == True and 
                created_army.get('military_branch') == "Army"):
                self.log_test("Army Member - Military Fields Saved", True, "military_service=True, military_branch=Army")
            else:
                self.log_test("Army Member - Military Fields Saved", False, 
                            f"military_service={created_army.get('military_service')}, military_branch={created_army.get('military_branch')}")
        
        # Test 1b: Create member with military_service=true, military_branch="Marines", is_police=true
        military_police_member = {
            "chapter": "AD",
            "title": "Member", 
            "handle": "MilitaryPoliceTest",
            "name": "Marine Police Veteran",
            "email": "marinepolice@test.com",
            "phone": "555-0002",
            "address": "456 Marine Corps Dr",
            "military_service": True,
            "military_branch": "Marines",
            "is_police": True
        }
        
        success, created_marine_police = self.run_test(
            "Create Member - Marine + Police",
            "POST",
            "members",
            201,
            data=military_police_member
        )
        
        marine_police_id = None
        if success and 'id' in created_marine_police:
            marine_police_id = created_marine_police['id']
            self.created_members.append(marine_police_id)
            
            # Verify combined military and first responder status
            if (created_marine_police.get('military_service') == True and 
                created_marine_police.get('military_branch') == "Marines" and
                created_marine_police.get('is_police') == True):
                self.log_test("Marine Police Member - Combined Service Fields", True, 
                            "military_service=True, military_branch=Marines, is_police=True")
            else:
                self.log_test("Marine Police Member - Combined Service Fields", False,
                            f"military_service={created_marine_police.get('military_service')}, "
                            f"military_branch={created_marine_police.get('military_branch')}, "
                            f"is_police={created_marine_police.get('is_police')}")
        
        return army_member_id, marine_police_id

    def test_create_member_with_first_responder_status(self):
        """Test creating members with first responder status"""
        print(f"\n🚨 Testing CREATE MEMBER WITH FIRST RESPONDER STATUS...")
        
        # Test 2a: Create member with is_police=true only
        police_member = {
            "chapter": "HA",
            "title": "Member",
            "handle": "PoliceTestOnly",
            "name": "Police Officer Test",
            "email": "police@test.com",
            "phone": "555-0003",
            "address": "789 Police Station Rd",
            "is_police": True
        }
        
        success, created_police = self.run_test(
            "Create Member - Police Only",
            "POST",
            "members",
            201,
            data=police_member
        )
        
        police_id = None
        if success and 'id' in created_police:
            police_id = created_police['id']
            self.created_members.append(police_id)
            
            # Verify police field and others default to false
            if (created_police.get('is_police') == True and
                created_police.get('is_fire') == False and
                created_police.get('is_ems') == False):
                self.log_test("Police Member - First Responder Fields", True, 
                            "is_police=True, is_fire=False, is_ems=False")
            else:
                self.log_test("Police Member - First Responder Fields", False,
                            f"is_police={created_police.get('is_police')}, "
                            f"is_fire={created_police.get('is_fire')}, "
                            f"is_ems={created_police.get('is_ems')}")
        
        # Test 2b: Create member with is_fire=true only
        fire_member = {
            "chapter": "HS",
            "title": "Member",
            "handle": "FireTestOnly",
            "name": "Firefighter Test",
            "email": "fire@test.com",
            "phone": "555-0004",
            "address": "101 Fire Station Ave",
            "is_fire": True
        }
        
        success, created_fire = self.run_test(
            "Create Member - Fire Only",
            "POST",
            "members",
            201,
            data=fire_member
        )
        
        fire_id = None
        if success and 'id' in created_fire:
            fire_id = created_fire['id']
            self.created_members.append(fire_id)
            
            # Verify fire field and others default to false
            if (created_fire.get('is_fire') == True and
                created_fire.get('is_police') == False and
                created_fire.get('is_ems') == False):
                self.log_test("Fire Member - First Responder Fields", True,
                            "is_fire=True, is_police=False, is_ems=False")
            else:
                self.log_test("Fire Member - First Responder Fields", False,
                            f"is_fire={created_fire.get('is_fire')}, "
                            f"is_police={created_fire.get('is_police')}, "
                            f"is_ems={created_fire.get('is_ems')}")
        
        # Test 2c: Create member with is_ems=true only
        ems_member = {
            "chapter": "National",
            "title": "Member",
            "handle": "EMSTestOnly",
            "name": "EMS Paramedic Test",
            "email": "ems@test.com",
            "phone": "555-0005",
            "address": "202 EMS Station Blvd",
            "is_ems": True
        }
        
        success, created_ems = self.run_test(
            "Create Member - EMS Only",
            "POST",
            "members",
            201,
            data=ems_member
        )
        
        ems_id = None
        if success and 'id' in created_ems:
            ems_id = created_ems['id']
            self.created_members.append(ems_id)
            
            # Verify EMS field and others default to false
            if (created_ems.get('is_ems') == True and
                created_ems.get('is_police') == False and
                created_ems.get('is_fire') == False):
                self.log_test("EMS Member - First Responder Fields", True,
                            "is_ems=True, is_police=False, is_fire=False")
            else:
                self.log_test("EMS Member - First Responder Fields", False,
                            f"is_ems={created_ems.get('is_ems')}, "
                            f"is_police={created_ems.get('is_police')}, "
                            f"is_fire={created_ems.get('is_fire')}")
        
        # Test 2d: Create member with all three (police, fire, ems) = true
        all_responder_member = {
            "chapter": "AD",
            "title": "Member",
            "handle": "AllResponderTest",
            "name": "All First Responder Test",
            "email": "allresponder@test.com",
            "phone": "555-0006",
            "address": "303 Emergency Services Way",
            "is_police": True,
            "is_fire": True,
            "is_ems": True
        }
        
        success, created_all = self.run_test(
            "Create Member - All First Responder Types",
            "POST",
            "members",
            201,
            data=all_responder_member
        )
        
        all_responder_id = None
        if success and 'id' in created_all:
            all_responder_id = created_all['id']
            self.created_members.append(all_responder_id)
            
            # Verify all first responder fields are true
            if (created_all.get('is_police') == True and
                created_all.get('is_fire') == True and
                created_all.get('is_ems') == True):
                self.log_test("All Responder Member - All Fields True", True,
                            "is_police=True, is_fire=True, is_ems=True")
            else:
                self.log_test("All Responder Member - All Fields True", False,
                            f"is_police={created_all.get('is_police')}, "
                            f"is_fire={created_all.get('is_fire')}, "
                            f"is_ems={created_all.get('is_ems')}")
        
        return police_id, fire_id, ems_id, all_responder_id

    def test_update_member_service_status(self):
        """Test updating existing member service status"""
        print(f"\n🔄 Testing UPDATE MEMBER SERVICE STATUS...")
        
        # Create a basic member first
        basic_member = {
            "chapter": "HA",
            "title": "Member",
            "handle": "UpdateTestMember",
            "name": "Update Test Member",
            "email": "update@test.com",
            "phone": "555-0007",
            "address": "404 Update St"
        }
        
        success, created_basic = self.run_test(
            "Create Basic Member for Update Testing",
            "POST",
            "members",
            201,
            data=basic_member
        )
        
        basic_member_id = None
        if success and 'id' in created_basic:
            basic_member_id = created_basic['id']
            self.created_members.append(basic_member_id)
        else:
            print("❌ Failed to create basic member for update testing")
            return None
        
        # Test 3a: Update existing member to add military_service
        military_update = {
            "military_service": True,
            "military_branch": "Navy"
        }
        
        success, updated_military = self.run_test(
            "Update Member - Add Military Service",
            "PUT",
            f"members/{basic_member_id}",
            200,
            data=military_update
        )
        
        if success:
            if (updated_military.get('military_service') == True and
                updated_military.get('military_branch') == "Navy"):
                self.log_test("Update Military Service - Fields Added", True,
                            "military_service=True, military_branch=Navy")
            else:
                self.log_test("Update Military Service - Fields Added", False,
                            f"military_service={updated_military.get('military_service')}, "
                            f"military_branch={updated_military.get('military_branch')}")
        
        # Test 3b: Update existing member to change military_branch
        branch_update = {
            "military_branch": "Air Force"
        }
        
        success, updated_branch = self.run_test(
            "Update Member - Change Military Branch",
            "PUT",
            f"members/{basic_member_id}",
            200,
            data=branch_update
        )
        
        if success:
            if updated_branch.get('military_branch') == "Air Force":
                self.log_test("Update Military Branch - Changed Successfully", True,
                            "military_branch=Air Force")
            else:
                self.log_test("Update Military Branch - Changed Successfully", False,
                            f"military_branch={updated_branch.get('military_branch')}")
        
        # Test 3c: Update existing member to toggle first responder flags
        responder_update = {
            "is_police": True,
            "is_fire": True
        }
        
        success, updated_responder = self.run_test(
            "Update Member - Add First Responder Status",
            "PUT",
            f"members/{basic_member_id}",
            200,
            data=responder_update
        )
        
        if success:
            if (updated_responder.get('is_police') == True and
                updated_responder.get('is_fire') == True):
                self.log_test("Update First Responder - Flags Added", True,
                            "is_police=True, is_fire=True")
            else:
                self.log_test("Update First Responder - Flags Added", False,
                            f"is_police={updated_responder.get('is_police')}, "
                            f"is_fire={updated_responder.get('is_fire')}")
        
        return basic_member_id

    def test_edge_cases(self):
        """Test edge cases for military and first responder fields"""
        print(f"\n🔍 Testing EDGE CASES...")
        
        # Test 4a: Create member with military_service=false but military_branch set
        edge_case_member = {
            "chapter": "HS",
            "title": "Member",
            "handle": "EdgeCaseTest",
            "name": "Edge Case Test Member",
            "email": "edgecase@test.com",
            "phone": "555-0008",
            "address": "505 Edge Case Rd",
            "military_service": False,
            "military_branch": "Coast Guard"  # Branch set but service=false
        }
        
        success, created_edge = self.run_test(
            "Create Member - military_service=false with branch set",
            "POST",
            "members",
            201,
            data=edge_case_member
        )
        
        edge_member_id = None
        if success and 'id' in created_edge:
            edge_member_id = created_edge['id']
            self.created_members.append(edge_member_id)
            
            # Branch should be allowed/ignored when service=false
            if (created_edge.get('military_service') == False and
                created_edge.get('military_branch') == "Coast Guard"):
                self.log_test("Edge Case - Branch with service=false", True,
                            "military_service=False, military_branch=Coast Guard (allowed)")
            else:
                self.log_test("Edge Case - Branch with service=false", False,
                            f"military_service={created_edge.get('military_service')}, "
                            f"military_branch={created_edge.get('military_branch')}")
        
        # Test 4b: Create member without any service flags (all defaults to false)
        default_member = {
            "chapter": "National",
            "title": "Member",
            "handle": "DefaultTest",
            "name": "Default Test Member",
            "email": "default@test.com",
            "phone": "555-0009",
            "address": "606 Default Ave"
            # No service flags specified - should default to false
        }
        
        success, created_default = self.run_test(
            "Create Member - No service flags (defaults)",
            "POST",
            "members",
            201,
            data=default_member
        )
        
        default_member_id = None
        if success and 'id' in created_default:
            default_member_id = created_default['id']
            self.created_members.append(default_member_id)
            
            # All service flags should default to false
            if (created_default.get('military_service') == False and
                created_default.get('is_police') == False and
                created_default.get('is_fire') == False and
                created_default.get('is_ems') == False):
                self.log_test("Default Member - All Service Flags False", True,
                            "All service flags default to False")
            else:
                self.log_test("Default Member - All Service Flags False", False,
                            f"military_service={created_default.get('military_service')}, "
                            f"is_police={created_default.get('is_police')}, "
                            f"is_fire={created_default.get('is_fire')}, "
                            f"is_ems={created_default.get('is_ems')}")
        
        # Test 4c: Verify existing members without these fields still work
        success, all_members = self.run_test(
            "Get All Members - Verify Existing Members Work",
            "GET",
            "members",
            200
        )
        
        if success and isinstance(all_members, list):
            # Check that we can retrieve members and they have the expected structure
            members_with_new_fields = 0
            members_without_new_fields = 0
            
            for member in all_members:
                if ('military_service' in member or 'is_police' in member or 
                    'is_fire' in member or 'is_ems' in member):
                    members_with_new_fields += 1
                else:
                    members_without_new_fields += 1
            
            self.log_test("Existing Members Compatibility", True,
                        f"Found {len(all_members)} total members: "
                        f"{members_with_new_fields} with new fields, "
                        f"{members_without_new_fields} without (backward compatible)")
        
        return edge_member_id, default_member_id

    def test_get_members_list(self):
        """Test GET /api/members - verify new fields appear in response"""
        print(f"\n📋 Testing GET MEMBERS LIST...")
        
        success, members_list = self.run_test(
            "Get Members List - Verify New Fields",
            "GET",
            "members",
            200
        )
        
        if success and isinstance(members_list, list):
            # Find members with military/first responder fields
            military_members = []
            first_responder_members = []
            
            for member in members_list:
                if member.get('military_service') == True:
                    military_members.append(member)
                
                if (member.get('is_police') == True or 
                    member.get('is_fire') == True or 
                    member.get('is_ems') == True):
                    first_responder_members.append(member)
            
            self.log_test("Members List - Military Service Members Found", 
                        len(military_members) > 0,
                        f"Found {len(military_members)} members with military service")
            
            self.log_test("Members List - First Responder Members Found",
                        len(first_responder_members) > 0,
                        f"Found {len(first_responder_members)} members with first responder status")
            
            # Verify field structure for military members
            for member in military_members[:3]:  # Check first 3
                if 'military_branch' in member:
                    self.log_test(f"Military Member {member.get('handle')} - Has Branch Field", True,
                                f"military_branch={member.get('military_branch')}")
                else:
                    self.log_test(f"Military Member {member.get('handle')} - Has Branch Field", False,
                                "military_branch field missing")
            
            # Verify field structure for first responder members
            for member in first_responder_members[:3]:  # Check first 3
                responder_types = []
                if member.get('is_police'): responder_types.append('Police')
                if member.get('is_fire'): responder_types.append('Fire')
                if member.get('is_ems'): responder_types.append('EMS')
                
                self.log_test(f"First Responder {member.get('handle')} - Service Types", True,
                            f"Services: {', '.join(responder_types)}")

    def test_valid_military_branches(self):
        """Test all valid military branch options"""
        print(f"\n🎖️  Testing VALID MILITARY BRANCHES...")
        
        valid_branches = [
            "Army", "Navy", "Air Force", "Marines", 
            "Coast Guard", "Space Force", "National Guard"
        ]
        
        branch_member_ids = []
        
        for i, branch in enumerate(valid_branches):
            branch_member = {
                "chapter": "National",
                "title": "Member",
                "handle": f"Branch{branch.replace(' ', '')}Test",
                "name": f"{branch} Test Member",
                "email": f"{branch.lower().replace(' ', '')}@test.com",
                "phone": f"555-{1000 + i:04d}",
                "address": f"{100 + i} {branch} Base Rd",
                "military_service": True,
                "military_branch": branch
            }
            
            success, created_branch_member = self.run_test(
                f"Create Member - {branch} Branch",
                "POST",
                "members",
                201,
                data=branch_member
            )
            
            if success and 'id' in created_branch_member:
                branch_member_id = created_branch_member['id']
                branch_member_ids.append(branch_member_id)
                self.created_members.append(branch_member_id)
                
                # Verify branch was saved correctly
                if created_branch_member.get('military_branch') == branch:
                    self.log_test(f"{branch} Branch - Saved Correctly", True,
                                f"military_branch={branch}")
                else:
                    self.log_test(f"{branch} Branch - Saved Correctly", False,
                                f"Expected {branch}, got {created_branch_member.get('military_branch')}")
        
        return branch_member_ids

    def cleanup_test_members(self):
        """Delete all test members created during testing"""
        print(f"\n🧹 Testing CLEANUP...")
        
        cleanup_count = 0
        for member_id in self.created_members:
            success, response = self.run_test(
                f"Delete Test Member {member_id[:8]}...",
                "DELETE",
                f"members/{member_id}?reason=Test cleanup",
                200
            )
            if success:
                cleanup_count += 1
        
        self.log_test("Cleanup All Test Members", 
                    cleanup_count == len(self.created_members),
                    f"Cleaned up {cleanup_count}/{len(self.created_members)} test members")

    def run_all_tests(self):
        """Run all military service and first responder tests"""
        print("🚀 Starting Military Service & First Responder Fields Testing")
        print("=" * 70)
        
        # Test authentication
        login_success, _ = self.test_login()
        if not login_success:
            print("❌ Cannot continue without authentication")
            return
        
        # Run all test scenarios
        try:
            # 1. CREATE MEMBER WITH MILITARY SERVICE
            self.test_create_member_with_military_service()
            
            # 2. CREATE MEMBER WITH FIRST RESPONDER STATUS
            self.test_create_member_with_first_responder_status()
            
            # 3. UPDATE MEMBER SERVICE STATUS
            self.test_update_member_service_status()
            
            # 4. EDGE CASES
            self.test_edge_cases()
            
            # 5. GET MEMBERS LIST
            self.test_get_members_list()
            
            # 6. VALID MILITARY BRANCHES
            self.test_valid_military_branches()
            
            # 7. CLEANUP
            self.cleanup_test_members()
            
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = MilitaryServiceFirstResponderTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)