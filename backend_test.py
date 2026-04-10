#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Fridge to Table App
Tests all endpoints including auth, pantry, recipes, scanning, grocery, profile, and stats
"""

import requests
import sys
import json
import base64
import os
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

class FridgeToTableAPITester:
    def __init__(self, base_url="https://fridge-to-table-25.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
        # MongoDB connection for creating test sessions
        self.mongo_client = MongoClient("mongodb://localhost:27017")
        self.db = self.mongo_client["test_database"]

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.failed_tests.append({"test": name, "error": details})

    def create_test_session(self):
        """Create a test user and session in MongoDB for auth-gated testing"""
        try:
            # Use the pre-created test session from the review request
            self.session_token = "test_session_screenshot_123"
            self.user_id = "test-user-screenshot"
            
            # Verify the session exists
            session = self.db.user_sessions.find_one({"session_token": self.session_token})
            if session:
                print(f"✅ Using existing test session for user: {self.user_id}")
                return True
            
            # Create test user if not exists
            test_user = {
                "user_id": self.user_id,
                "email": "test@example.com",
                "name": "Test User Screenshot",
                "picture": "https://example.com/avatar.jpg",
                "allergies": ["Peanuts"],
                "dietary_preferences": ["Vegetarian"],
                "skill_level": "beginner",
                "default_servings": 2,
                "calorie_target": 2000,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Insert or update user
            self.db.users.replace_one({"user_id": "test_user_123"}, test_user, upsert=True)
            
            # Create test session
            test_session = {
                "user_id": "test_user_123",
                "session_token": "test_session_token_123",
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Insert session
            self.db.user_sessions.replace_one({"session_token": "test_session_token_123"}, test_session, upsert=True)
            
            self.session_token = "test_session_token_123"
            self.user_id = "test_user_123"
            print("✅ Test session created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test session: {e}")
            return False

    def make_request(self, method, endpoint, data=None, files=None, auth_required=True, timeout=30):
        """Make HTTP request with optional authentication"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, headers=headers, files=files, timeout=timeout)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
            
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test /auth/me without authentication (should return 401)
        response = self.make_request('GET', 'auth/me', auth_required=False)
        if response and response.status_code == 401:
            self.log_test("GET /auth/me (unauthenticated)", True)
        else:
            self.log_test("GET /auth/me (unauthenticated)", False, f"Expected 401, got {response.status_code if response else 'No response'}")
        
        # Test /auth/me with authentication (should return user data)
        response = self.make_request('GET', 'auth/me')
        if response and response.status_code == 200:
            try:
                user_data = response.json()
                if user_data.get('user_id') == self.user_id:
                    self.log_test("GET /auth/me (authenticated)", True)
                else:
                    self.log_test("GET /auth/me (authenticated)", False, "User data mismatch")
            except:
                self.log_test("GET /auth/me (authenticated)", False, "Invalid JSON response")
        else:
            self.log_test("GET /auth/me (authenticated)", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_pantry_endpoints(self):
        """Test pantry CRUD operations"""
        print("\n📦 Testing Pantry Endpoints...")
        
        # Test GET /pantry (should return empty list initially)
        response = self.make_request('GET', 'pantry')
        if response and response.status_code == 200:
            self.log_test("GET /pantry", True)
            pantry_items = response.json()
        else:
            self.log_test("GET /pantry", False, f"Expected 200, got {response.status_code if response else 'No response'}")
            return
        
        # Test POST /pantry (add single item)
        test_item = {
            "name": "Test Chicken Breast",
            "category": "protein",
            "quantity": "2",
            "unit": "lbs",
            "expiry_date": "2024-12-31",
            "notes": "Fresh from store"
        }
        
        response = self.make_request('POST', 'pantry', data=test_item)
        if response and response.status_code == 200:
            try:
                created_item = response.json()
                item_id = created_item.get('item_id')
                if item_id:
                    self.log_test("POST /pantry", True)
                    self.test_item_id = item_id
                else:
                    self.log_test("POST /pantry", False, "No item_id in response")
                    return
            except:
                self.log_test("POST /pantry", False, "Invalid JSON response")
                return
        else:
            self.log_test("POST /pantry", False, f"Expected 200, got {response.status_code if response else 'No response'}")
            return
        
        # Test POST /pantry/bulk (add multiple items)
        bulk_items = {
            "items": [
                {"name": "Tomatoes", "category": "vegetable", "quantity": "5"},
                {"name": "Bread", "category": "grain", "quantity": "1", "unit": "loaf"}
            ]
        }
        
        response = self.make_request('POST', 'pantry/bulk', data=bulk_items)
        if response and response.status_code == 200:
            try:
                result = response.json()
                if result.get('count') == 2:
                    self.log_test("POST /pantry/bulk", True)
                else:
                    self.log_test("POST /pantry/bulk", False, f"Expected count 2, got {result.get('count')}")
            except:
                self.log_test("POST /pantry/bulk", False, "Invalid JSON response")
        else:
            self.log_test("POST /pantry/bulk", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test PUT /pantry/{item_id} (update item)
        update_data = {"quantity": "3", "notes": "Updated quantity"}
        response = self.make_request('PUT', f'pantry/{self.test_item_id}', data=update_data)
        if response and response.status_code == 200:
            self.log_test("PUT /pantry/{item_id}", True)
        else:
            self.log_test("PUT /pantry/{item_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE /pantry/{item_id}
        response = self.make_request('DELETE', f'pantry/{self.test_item_id}')
        if response and response.status_code == 200:
            self.log_test("DELETE /pantry/{item_id}", True)
        else:
            self.log_test("DELETE /pantry/{item_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_recipe_endpoints(self):
        """Test recipe generation and saved recipes"""
        print("\n🍳 Testing Recipe Endpoints...")
        
        # Test POST /recipes/generate
        recipe_request = {
            "ingredients": ["chicken", "tomatoes", "onions"],
            "max_time": 30,
            "budget": "moderate",
            "skill_level": "beginner",
            "dietary_restrictions": [],
            "servings": 2,
            "calorie_target": 500,
            "cuisine": "Italian",
            "meal_type": "dinner"
        }
        
        print("⏳ Generating recipes with AI (this may take 10-15 seconds)...")
        response = self.make_request('POST', 'recipes/generate', data=recipe_request)
        if response and response.status_code == 200:
            try:
                result = response.json()
                recipes = result.get('recipes', [])
                if len(recipes) > 0:
                    self.log_test("POST /recipes/generate", True)
                    self.test_recipe = recipes[0]  # Save first recipe for testing save functionality
                else:
                    self.log_test("POST /recipes/generate", False, "No recipes generated")
                    return
            except:
                self.log_test("POST /recipes/generate", False, "Invalid JSON response")
                return
        else:
            self.log_test("POST /recipes/generate", False, f"Expected 200, got {response.status_code if response else 'No response'}")
            return
        
        # Test POST /recipes/save
        save_data = {"recipe": self.test_recipe}
        response = self.make_request('POST', 'recipes/save', data=save_data)
        if response and response.status_code == 200:
            try:
                saved_recipe = response.json()
                self.saved_recipe_id = saved_recipe.get('saved_id')
                if self.saved_recipe_id:
                    self.log_test("POST /recipes/save", True)
                else:
                    self.log_test("POST /recipes/save", False, "No saved_id in response")
                    return
            except:
                self.log_test("POST /recipes/save", False, "Invalid JSON response")
                return
        else:
            self.log_test("POST /recipes/save", False, f"Expected 200, got {response.status_code if response else 'No response'}")
            return
        
        # Test GET /recipes/saved
        response = self.make_request('GET', 'recipes/saved')
        if response and response.status_code == 200:
            try:
                saved_recipes = response.json()
                if len(saved_recipes) > 0:
                    self.log_test("GET /recipes/saved", True)
                else:
                    self.log_test("GET /recipes/saved", False, "No saved recipes found")
            except:
                self.log_test("GET /recipes/saved", False, "Invalid JSON response")
        else:
            self.log_test("GET /recipes/saved", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE /recipes/saved/{saved_id}
        response = self.make_request('DELETE', f'recipes/saved/{self.saved_recipe_id}')
        if response and response.status_code == 200:
            self.log_test("DELETE /recipes/saved/{saved_id}", True)
        else:
            self.log_test("DELETE /recipes/saved/{saved_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_scan_endpoints(self):
        """Test photo and receipt scanning endpoints"""
        print("\n📷 Testing Scan Endpoints...")
        
        # Create a simple test image (base64 encoded)
        # This is a minimal 1x1 pixel JPEG image
        test_image_b64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
        test_image_data = base64.b64decode(test_image_b64)
        
        # Test POST /scan/photo
        print("⏳ Scanning photo with AI (this may take 10-15 seconds)...")
        files = {'file': ('test_image.jpg', test_image_data, 'image/jpeg')}
        response = self.make_request('POST', 'scan/photo', files=files)
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'items' in result:
                    self.log_test("POST /scan/photo", True)
                else:
                    self.log_test("POST /scan/photo", False, "No items in response")
            except:
                self.log_test("POST /scan/photo", False, "Invalid JSON response")
        else:
            self.log_test("POST /scan/photo", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test POST /scan/receipt
        print("⏳ Scanning receipt with AI (this may take 10-15 seconds)...")
        files = {'file': ('test_receipt.jpg', test_image_data, 'image/jpeg')}
        response = self.make_request('POST', 'scan/receipt', files=files)
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'items' in result:
                    self.log_test("POST /scan/receipt", True)
                else:
                    self.log_test("POST /scan/receipt", False, "No items in response")
            except:
                self.log_test("POST /scan/receipt", False, "Invalid JSON response")
        else:
            self.log_test("POST /scan/receipt", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_grocery_endpoints(self):
        """Test grocery suggestions endpoint"""
        print("\n🛒 Testing Grocery Endpoints...")
        
        grocery_request = {
            "pantry_ingredients": ["chicken", "rice"],
            "preferences": ["healthy", "quick"],
            "budget": "moderate"
        }
        
        print("⏳ Generating grocery suggestions with AI (this may take 10-15 seconds)...")
        response = self.make_request('POST', 'grocery/suggestions', data=grocery_request)
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'suggestions' in result:
                    self.log_test("POST /grocery/suggestions", True)
                else:
                    self.log_test("POST /grocery/suggestions", False, "No suggestions in response")
            except:
                self.log_test("POST /grocery/suggestions", False, "Invalid JSON response")
        else:
            self.log_test("POST /grocery/suggestions", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test NEW priced suggestions endpoint
        print("⏳ Generating priced grocery suggestions with AI (this may take 10-15 seconds)...")
        response = self.make_request('POST', 'grocery/suggestions-priced', data=grocery_request)
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'suggestions' in result and len(result['suggestions']) > 0:
                    # Check if suggestions have estimated_price field
                    first_suggestion = result['suggestions'][0]
                    if 'estimated_price' in first_suggestion:
                        self.log_test("POST /grocery/suggestions-priced", True)
                        self.test_suggestions = result['suggestions'][:3]  # Save first 3 for cart testing
                    else:
                        self.log_test("POST /grocery/suggestions-priced", False, "Suggestions missing estimated_price field")
                else:
                    self.log_test("POST /grocery/suggestions-priced", False, "No suggestions in response")
            except:
                self.log_test("POST /grocery/suggestions-priced", False, "Invalid JSON response")
        else:
            self.log_test("POST /grocery/suggestions-priced", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_profile_endpoints(self):
        """Test profile management endpoints"""
        print("\n👤 Testing Profile Endpoints...")
        
        # Test GET /profile
        response = self.make_request('GET', 'profile')
        if response and response.status_code == 200:
            try:
                profile = response.json()
                if profile.get('user_id') == self.user_id:
                    self.log_test("GET /profile", True)
                else:
                    self.log_test("GET /profile", False, "Profile data mismatch")
            except:
                self.log_test("GET /profile", False, "Invalid JSON response")
        else:
            self.log_test("GET /profile", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test PUT /profile
        profile_update = {
            "allergies": ["Peanuts", "Shellfish"],
            "dietary_preferences": ["Vegetarian", "Gluten-Free"],
            "skill_level": "intermediate",
            "default_servings": 4,
            "calorie_target": 2200
        }
        
        response = self.make_request('PUT', 'profile', data=profile_update)
        if response and response.status_code == 200:
            try:
                updated_profile = response.json()
                if updated_profile.get('skill_level') == 'intermediate':
                    self.log_test("PUT /profile", True)
                else:
                    self.log_test("PUT /profile", False, "Profile update failed")
            except:
                self.log_test("PUT /profile", False, "Invalid JSON response")
        else:
            self.log_test("PUT /profile", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        print("\n📊 Testing Stats Endpoint...")
        
        response = self.make_request('GET', 'stats')
        if response and response.status_code == 200:
            try:
                stats = response.json()
                required_fields = ['pantry_count', 'saved_recipes_count', 'categories']
                if all(field in stats for field in required_fields):
                    self.log_test("GET /stats", True)
                else:
                    self.log_test("GET /stats", False, f"Missing required fields in stats")
            except:
                self.log_test("GET /stats", False, "Invalid JSON response")
        else:
            self.log_test("GET /stats", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_barcode_endpoints(self):
        """Test barcode scanning endpoints (NEW FEATURE)"""
        print("\n📱 Testing Barcode Scanner Endpoints...")
        
        # Test valid barcode (Coca-Cola)
        response = self.make_request('GET', 'barcode/5449000000996')
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get('found') == True and 'Original Taste' in data.get('name', ''):
                    self.log_test("GET /barcode/5449000000996 (valid)", True)
                else:
                    self.log_test("GET /barcode/5449000000996 (valid)", False, f"Expected found:true with 'Original Taste', got: {data}")
            except:
                self.log_test("GET /barcode/5449000000996 (valid)", False, "Invalid JSON response")
        else:
            self.log_test("GET /barcode/5449000000996 (valid)", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test invalid barcode
        response = self.make_request('GET', 'barcode/0000000000000')
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get('found') == False:
                    self.log_test("GET /barcode/0000000000000 (invalid)", True)
                else:
                    self.log_test("GET /barcode/0000000000000 (invalid)", False, f"Expected found:false, got: {data}")
            except:
                self.log_test("GET /barcode/0000000000000 (invalid)", False, "Invalid JSON response")
        else:
            self.log_test("GET /barcode/0000000000000 (invalid)", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_notification_endpoints(self):
        """Test expiry notification endpoints (NEW FEATURE)"""
        print("\n🔔 Testing Expiry Notification Endpoints...")
        
        response = self.make_request('GET', 'notifications/expiring')
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'notifications' in data and 'count' in data:
                    self.log_test("GET /notifications/expiring", True)
                    print(f"   Found {data.get('count', 0)} expiring items")
                else:
                    self.log_test("GET /notifications/expiring", False, f"Missing notifications or count fields: {data}")
            except:
                self.log_test("GET /notifications/expiring", False, "Invalid JSON response")
        else:
            self.log_test("GET /notifications/expiring", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_cart_endpoints(self):
        """Test grocery cart endpoints (NEW FEATURE)"""
        print("\n🛒 Testing Grocery Cart Endpoints...")
        
        # Test GET /cart (should be empty initially)
        response = self.make_request('GET', 'cart')
        if response and response.status_code == 200:
            try:
                cart_data = response.json()
                required_fields = ['items', 'subtotal', 'service_fee', 'total', 'item_count']
                if all(field in cart_data for field in required_fields):
                    self.log_test("GET /cart", True)
                    print(f"   Cart has {cart_data.get('item_count', 0)} items, total: ${cart_data.get('total', 0):.2f}")
                else:
                    self.log_test("GET /cart", False, f"Missing required fields: {required_fields}")
            except:
                self.log_test("GET /cart", False, "Invalid JSON response")
        else:
            self.log_test("GET /cart", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test POST /cart/add (add single item)
        test_item = {
            "name": "Test Chicken Breast",
            "category": "protein",
            "estimated_price": 8.99
        }
        
        response = self.make_request('POST', 'cart/add', data=test_item)
        if response and response.status_code == 200:
            try:
                added_item = response.json()
                if 'cart_item_id' in added_item and added_item.get('name') == test_item['name']:
                    self.log_test("POST /cart/add", True)
                    self.test_cart_item_id = added_item['cart_item_id']
                else:
                    self.log_test("POST /cart/add", False, "Missing cart_item_id or name mismatch")
            except:
                self.log_test("POST /cart/add", False, "Invalid JSON response")
        else:
            self.log_test("POST /cart/add", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test POST /cart/add-bulk (add multiple items)
        if hasattr(self, 'test_suggestions') and self.test_suggestions:
            bulk_items = {
                "items": [
                    {
                        "name": item.get('name', 'Unknown Item'),
                        "category": item.get('category', 'other'),
                        "estimated_price": item.get('estimated_price', 0)
                    } for item in self.test_suggestions
                ]
            }
        else:
            # Fallback if no suggestions available
            bulk_items = {
                "items": [
                    {"name": "Tomatoes", "category": "vegetable", "estimated_price": 3.49},
                    {"name": "Bread", "category": "grain", "estimated_price": 2.99}
                ]
            }
        
        response = self.make_request('POST', 'cart/add-bulk', data=bulk_items)
        if response and response.status_code == 200:
            try:
                result = response.json()
                expected_count = len(bulk_items['items'])
                if result.get('count') == expected_count:
                    self.log_test("POST /cart/add-bulk", True)
                    print(f"   Added {expected_count} items to cart")
                else:
                    self.log_test("POST /cart/add-bulk", False, f"Expected count {expected_count}, got {result.get('count')}")
            except:
                self.log_test("POST /cart/add-bulk", False, "Invalid JSON response")
        else:
            self.log_test("POST /cart/add-bulk", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test GET /cart again (should have items now)
        response = self.make_request('GET', 'cart')
        if response and response.status_code == 200:
            try:
                cart_data = response.json()
                if cart_data.get('item_count', 0) > 0:
                    self.log_test("GET /cart (with items)", True)
                    print(f"   Cart now has {cart_data.get('item_count', 0)} items, subtotal: ${cart_data.get('subtotal', 0):.2f}, total: ${cart_data.get('total', 0):.2f}")
                    # Verify service fee calculation
                    expected_total = cart_data.get('subtotal', 0) + cart_data.get('service_fee', 0)
                    if abs(cart_data.get('total', 0) - expected_total) < 0.01:
                        self.log_test("Cart total calculation", True)
                    else:
                        self.log_test("Cart total calculation", False, f"Expected {expected_total:.2f}, got {cart_data.get('total', 0):.2f}")
                else:
                    self.log_test("GET /cart (with items)", False, "Cart should have items but is empty")
            except:
                self.log_test("GET /cart (with items)", False, "Invalid JSON response")
        else:
            self.log_test("GET /cart (with items)", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE /cart/{cart_item_id} (remove single item)
        if hasattr(self, 'test_cart_item_id'):
            response = self.make_request('DELETE', f'cart/{self.test_cart_item_id}')
            if response and response.status_code == 200:
                self.log_test("DELETE /cart/{cart_item_id}", True)
            else:
                self.log_test("DELETE /cart/{cart_item_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE /cart (clear entire cart)
        response = self.make_request('DELETE', 'cart')
        if response and response.status_code == 200:
            self.log_test("DELETE /cart (clear all)", True)
        else:
            self.log_test("DELETE /cart (clear all)", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_store_endpoints(self):
        """Test store listing endpoints (NEW FEATURE)"""
        print("\n🏪 Testing Store Endpoints...")
        
        response = self.make_request('GET', 'stores')
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'stores' in data and len(data['stores']) > 0:
                    stores = data['stores']
                    expected_stores = ['instacart', 'walmart', 'shoprite', 'amazon_fresh', 'target']
                    store_ids = [store.get('id') for store in stores]
                    if all(store_id in store_ids for store_id in expected_stores):
                        self.log_test("GET /stores", True)
                        print(f"   Found {len(stores)} stores: {', '.join(store_ids)}")
                    else:
                        self.log_test("GET /stores", False, f"Missing expected stores. Found: {store_ids}")
                else:
                    self.log_test("GET /stores", False, "No stores in response")
            except:
                self.log_test("GET /stores", False, "Invalid JSON response")
        else:
            self.log_test("GET /stores", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def test_checkout_endpoints(self):
        """Test Stripe checkout endpoints (NEW FEATURE)"""
        print("\n💳 Testing Stripe Checkout Endpoints...")
        
        # First add some items to cart for checkout testing
        test_items = [
            {"name": "Test Item 1", "category": "protein", "estimated_price": 5.99},
            {"name": "Test Item 2", "category": "vegetable", "estimated_price": 3.49}
        ]
        
        for item in test_items:
            response = self.make_request('POST', 'cart/add', data=item)
            if not (response and response.status_code == 200):
                print(f"   ⚠️ Failed to add test item for checkout: {item['name']}")
        
        # Test POST /cart/checkout (create Stripe session)
        checkout_data = {
            "origin_url": "https://fridge-to-table-25.preview.emergentagent.com",
            "store_id": "instacart"
        }
        
        response = self.make_request('POST', 'cart/checkout', data=checkout_data)
        session_id = None
        if response and response.status_code == 200:
            try:
                result = response.json()
                if 'url' in result and 'session_id' in result:
                    session_id = result['session_id']
                    self.log_test("POST /cart/checkout", True)
                    print(f"   Created Stripe session: {session_id}")
                    print(f"   Checkout URL: {result['url'][:50]}...")
                else:
                    self.log_test("POST /cart/checkout", False, "Missing url or session_id in response")
            except:
                self.log_test("POST /cart/checkout", False, "Invalid JSON response")
        else:
            self.log_test("POST /cart/checkout", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test GET /cart/checkout/status/{session_id}
        if session_id:
            response = self.make_request('GET', f'cart/checkout/status/{session_id}')
            if response and response.status_code == 200:
                try:
                    status_data = response.json()
                    required_fields = ['status', 'payment_status']
                    if all(field in status_data for field in required_fields):
                        self.log_test("GET /cart/checkout/status/{session_id}", True)
                        print(f"   Payment status: {status_data.get('payment_status')}, Session status: {status_data.get('status')}")
                    else:
                        self.log_test("GET /cart/checkout/status/{session_id}", False, f"Missing required fields: {required_fields}")
                except:
                    self.log_test("GET /cart/checkout/status/{session_id}", False, "Invalid JSON response")
            else:
                self.log_test("GET /cart/checkout/status/{session_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Clean up - clear cart
        self.make_request('DELETE', 'cart')

    def test_meal_plan_endpoints(self):
        """Test meal planner endpoints (NEW FEATURE)"""
        print("\n📅 Testing Meal Planner Endpoints...")
        
        # Test GET meal plan
        response = self.make_request('GET', 'mealplan')
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.log_test("GET /mealplan", True)
                print(f"   Found {len(data) if isinstance(data, list) else 'unknown'} meal plan entries")
            except:
                self.log_test("GET /mealplan", False, "Invalid JSON response")
        else:
            self.log_test("GET /mealplan", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test POST meal plan entry
        meal_entry = {
            "day": "Monday",
            "meal_type": "breakfast", 
            "recipe": {
                "title": "Test Breakfast",
                "description": "A test meal for API testing",
                "total_time": 15,
                "calories_per_serving": 300,
                "ingredients_used": ["eggs", "bread"],
                "ingredients_needed": [],
                "instructions": ["Cook eggs", "Toast bread"]
            }
        }
        
        response = self.make_request('POST', 'mealplan', meal_entry)
        entry_id = None
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'entry_id' in data:
                    entry_id = data['entry_id']
                    self.log_test("POST /mealplan", True)
                else:
                    self.log_test("POST /mealplan", False, "Missing entry_id in response")
            except:
                self.log_test("POST /mealplan", False, "Invalid JSON response")
        else:
            self.log_test("POST /mealplan", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE specific meal plan entry
        if entry_id:
            response = self.make_request('DELETE', f'mealplan/{entry_id}')
            if response and response.status_code == 200:
                self.log_test("DELETE /mealplan/{entry_id}", True)
            else:
                self.log_test("DELETE /mealplan/{entry_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE all meal plan entries
        response = self.make_request('DELETE', 'mealplan')
        if response and response.status_code == 200:
            self.log_test("DELETE /mealplan (clear all)", True)
        else:
            self.log_test("DELETE /mealplan (clear all)", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test AI meal plan generation (this is slow)
        print("   🤖 Testing AI meal plan generation (may take 15-30 seconds)...")
        response = self.make_request('POST', 'mealplan/generate', {"days": ["Monday", "Tuesday"]}, timeout=45)
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'meal_plan' in data:
                    self.log_test("POST /mealplan/generate", True)
                    print(f"   Generated meal plan with {len(data.get('shopping_list', []))} shopping items")
                else:
                    self.log_test("POST /mealplan/generate", False, f"Missing meal_plan field: {data}")
            except:
                self.log_test("POST /mealplan/generate", False, "Invalid JSON response")
        else:
            self.log_test("POST /mealplan/generate", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        """Test meal planner endpoints (NEW FEATURE)"""
        print("\n📅 Testing Meal Planner Endpoints...")
        
        # Test GET meal plan
        response = self.make_request('GET', 'mealplan')
        if response and response.status_code == 200:
            try:
                data = response.json()
                self.log_test("GET /mealplan", True)
                print(f"   Found {len(data) if isinstance(data, list) else 'unknown'} meal plan entries")
            except:
                self.log_test("GET /mealplan", False, "Invalid JSON response")
        else:
            self.log_test("GET /mealplan", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test POST meal plan entry
        meal_entry = {
            "day": "Monday",
            "meal_type": "breakfast", 
            "recipe": {
                "title": "Test Breakfast",
                "description": "A test meal for API testing",
                "total_time": 15,
                "calories_per_serving": 300,
                "ingredients_used": ["eggs", "bread"],
                "ingredients_needed": [],
                "instructions": ["Cook eggs", "Toast bread"]
            }
        }
        
        response = self.make_request('POST', 'mealplan', meal_entry)
        entry_id = None
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'entry_id' in data:
                    entry_id = data['entry_id']
                    self.log_test("POST /mealplan", True)
                else:
                    self.log_test("POST /mealplan", False, "Missing entry_id in response")
            except:
                self.log_test("POST /mealplan", False, "Invalid JSON response")
        else:
            self.log_test("POST /mealplan", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE specific meal plan entry
        if entry_id:
            response = self.make_request('DELETE', f'mealplan/{entry_id}')
            if response and response.status_code == 200:
                self.log_test("DELETE /mealplan/{entry_id}", True)
            else:
                self.log_test("DELETE /mealplan/{entry_id}", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test DELETE all meal plan entries
        response = self.make_request('DELETE', 'mealplan')
        if response and response.status_code == 200:
            self.log_test("DELETE /mealplan (clear all)", True)
        else:
            self.log_test("DELETE /mealplan (clear all)", False, f"Expected 200, got {response.status_code if response else 'No response'}")
        
        # Test AI meal plan generation (this is slow)
        print("   🤖 Testing AI meal plan generation (may take 15-30 seconds)...")
        response = self.make_request('POST', 'mealplan/generate', {"days": ["Monday", "Tuesday"]}, timeout=45)
        if response and response.status_code == 200:
            try:
                data = response.json()
                if 'meal_plan' in data:
                    self.log_test("POST /mealplan/generate", True)
                    print(f"   Generated meal plan with {len(data.get('shopping_list', []))} shopping items")
                else:
                    self.log_test("POST /mealplan/generate", False, f"Missing meal_plan field: {data}")
            except:
                self.log_test("POST /mealplan/generate", False, "Invalid JSON response")
        else:
            self.log_test("POST /mealplan/generate", False, f"Expected 200, got {response.status_code if response else 'No response'}")

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Fridge to Table Backend API Tests...")
        print(f"🌐 Testing against: {self.base_url}")
        
        # Create test session first
        if not self.create_test_session():
            print("❌ Cannot proceed without test session")
            return False
        
        # Run all test suites
        self.test_auth_endpoints()
        self.test_pantry_endpoints()
        self.test_recipe_endpoints()
        self.test_scan_endpoints()
        self.test_grocery_endpoints()
        self.test_profile_endpoints()
        self.test_stats_endpoint()
        
        # NEW FEATURES TESTING
        self.test_barcode_endpoints()
        self.test_notification_endpoints()
        self.test_meal_plan_endpoints()
        
        # GROCERY CART & CHECKOUT FEATURES (NEWEST)
        self.test_cart_endpoints()
        self.test_store_endpoints()
        self.test_checkout_endpoints()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"✅ Passed: {self.tests_passed}/{self.tests_run}")
        print(f"❌ Failed: {len(self.failed_tests)}/{self.tests_run}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        # Cleanup
        try:
            self.mongo_client.close()
        except:
            pass
        
        return success_rate >= 80  # Consider 80%+ success rate as passing

def main():
    """Main test execution"""
    tester = FridgeToTableAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())