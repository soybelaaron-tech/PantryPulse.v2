"""
Comprehensive test suite for all API routes after backend refactor.
Tests: pantry CRUD, recipes, profile, stats, notifications, mealplan, cart, stores
"""
import pytest
import requests
import uuid
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fridge-to-table-25.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@pantrypulse.com"
ADMIN_PASSWORD = "PantryPulse2024!"


@pytest.fixture(scope="module")
def auth_session():
    """Create authenticated session for all tests"""
    session = requests.Session()
    login_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    response = session.post(f"{BASE_URL}/api/auth/login", json=login_payload)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return session


# ========== PANTRY CRUD TESTS ==========

class TestPantryCRUD:
    """Test pantry CRUD operations"""
    
    def test_get_pantry_items(self, auth_session):
        """GET /api/pantry - returns list of pantry items"""
        response = auth_session.get(f"{BASE_URL}/api/pantry")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/pantry returns {len(data)} items")
    
    def test_add_pantry_item(self, auth_session):
        """POST /api/pantry - adds single item"""
        unique_name = f"TEST_Item_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "category": "vegetable",
            "quantity": "2",
            "unit": "lbs"
        }
        response = auth_session.post(f"{BASE_URL}/api/pantry", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "item_id" in data, "Response should contain item_id"
        assert data["name"] == unique_name, "Name should match"
        assert data["category"] == "vegetable", "Category should match"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/pantry/{data['item_id']}")
        print(f"✓ POST /api/pantry creates item: {unique_name}")
    
    def test_update_pantry_item(self, auth_session):
        """PUT /api/pantry/{item_id} - updates item"""
        # Create item first
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:6]}"
        create_payload = {"name": unique_name, "category": "fruit", "quantity": "5", "unit": "pcs"}
        create_response = auth_session.post(f"{BASE_URL}/api/pantry", json=create_payload)
        assert create_response.status_code == 200
        item_id = create_response.json()["item_id"]
        
        # Update item
        update_payload = {"quantity": "10", "notes": "Updated via test"}
        update_response = auth_session.put(f"{BASE_URL}/api/pantry/{item_id}", json=update_payload)
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        data = update_response.json()
        
        assert data["quantity"] == "10", "Quantity should be updated"
        assert data["notes"] == "Updated via test", "Notes should be updated"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/pantry/{item_id}")
        print(f"✓ PUT /api/pantry/{item_id} updates item")
    
    def test_delete_pantry_item(self, auth_session):
        """DELETE /api/pantry/{item_id} - deletes item"""
        # Create item first
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:6]}"
        create_payload = {"name": unique_name, "category": "grain"}
        create_response = auth_session.post(f"{BASE_URL}/api/pantry", json=create_payload)
        assert create_response.status_code == 200
        item_id = create_response.json()["item_id"]
        
        # Delete item
        delete_response = auth_session.delete(f"{BASE_URL}/api/pantry/{item_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        data = delete_response.json()
        assert data.get("message") == "Deleted", "Should return deleted message"
        
        # Verify deletion
        get_response = auth_session.get(f"{BASE_URL}/api/pantry")
        items = get_response.json()
        assert not any(i["item_id"] == item_id for i in items), "Item should be deleted"
        print(f"✓ DELETE /api/pantry/{item_id} removes item")
    
    def test_bulk_add_pantry_items(self, auth_session):
        """POST /api/pantry/bulk - adds multiple items"""
        unique_suffix = uuid.uuid4().hex[:6]
        payload = {
            "items": [
                {"name": f"TEST_Bulk1_{unique_suffix}", "category": "dairy"},
                {"name": f"TEST_Bulk2_{unique_suffix}", "category": "protein"},
                {"name": f"TEST_Bulk3_{unique_suffix}", "category": "vegetable"}
            ]
        }
        response = auth_session.post(f"{BASE_URL}/api/pantry/bulk", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "added" in data, "Response should contain 'added'"
        assert "count" in data, "Response should contain 'count'"
        assert data["count"] == 3, "Should have added 3 items"
        
        # Cleanup
        for item in data["added"]:
            auth_session.delete(f"{BASE_URL}/api/pantry/{item['item_id']}")
        print(f"✓ POST /api/pantry/bulk adds {data['count']} items")


# ========== RECIPE TESTS ==========

class TestRecipes:
    """Test recipe endpoints"""
    
    def test_generate_recipes(self, auth_session):
        """POST /api/recipes/generate - generates AI recipes"""
        payload = {
            "ingredients": ["chicken", "rice", "broccoli"],
            "servings": 2
        }
        response = auth_session.post(f"{BASE_URL}/api/recipes/generate", json=payload, timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "recipes" in data, "Response should contain 'recipes'"
        assert isinstance(data["recipes"], list), "Recipes should be a list"
        if data["recipes"]:
            recipe = data["recipes"][0]
            assert "title" in recipe, "Recipe should have title"
            assert "recipe_id" in recipe, "Recipe should have recipe_id"
        print(f"✓ POST /api/recipes/generate returns {len(data['recipes'])} recipes")
    
    def test_get_saved_recipes(self, auth_session):
        """GET /api/recipes/saved - returns saved recipes"""
        response = auth_session.get(f"{BASE_URL}/api/recipes/saved")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/recipes/saved returns {len(data)} recipes")
    
    def test_save_recipe(self, auth_session):
        """POST /api/recipes/save - saves a recipe"""
        payload = {
            "recipe": {
                "title": f"TEST_Recipe_{uuid.uuid4().hex[:6]}",
                "description": "Test recipe description",
                "instructions": ["Step 1", "Step 2"],
                "ingredients_used": ["chicken", "rice"]
            }
        }
        response = auth_session.post(f"{BASE_URL}/api/recipes/save", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "saved_id" in data, "Response should contain saved_id"
        assert data["title"] == payload["recipe"]["title"], "Title should match"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/recipes/saved/{data['saved_id']}")
        print(f"✓ POST /api/recipes/save saves recipe: {data['title']}")
    
    def test_cook_recipe(self, auth_session):
        """POST /api/recipes/cook - deducts ingredients"""
        # First add some test items to pantry
        unique_suffix = uuid.uuid4().hex[:6]
        items_to_add = [
            {"name": f"TEST_Cook_Chicken_{unique_suffix}", "category": "protein"},
            {"name": f"TEST_Cook_Rice_{unique_suffix}", "category": "grain"}
        ]
        added_ids = []
        for item in items_to_add:
            resp = auth_session.post(f"{BASE_URL}/api/pantry", json=item)
            if resp.status_code == 200:
                added_ids.append(resp.json()["item_id"])
        
        # Cook recipe
        payload = {
            "ingredients_used": [f"TEST_Cook_Chicken_{unique_suffix}", f"TEST_Cook_Rice_{unique_suffix}"]
        }
        response = auth_session.post(f"{BASE_URL}/api/recipes/cook", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "removed" in data, "Response should contain 'removed'"
        assert "not_found" in data, "Response should contain 'not_found'"
        assert "message" in data, "Response should contain 'message'"
        print(f"✓ POST /api/recipes/cook - removed: {len(data['removed'])}, not_found: {len(data['not_found'])}")


# ========== PROFILE TESTS ==========

class TestProfile:
    """Test profile endpoints"""
    
    def test_get_profile(self, auth_session):
        """GET /api/profile - returns user profile"""
        response = auth_session.get(f"{BASE_URL}/api/profile")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "user_id" in data, "Response should contain user_id"
        assert "email" in data, "Response should contain email"
        assert "password_hash" not in data, "password_hash should NOT be in response"
        print(f"✓ GET /api/profile returns profile for: {data['email']}")
    
    def test_update_profile(self, auth_session):
        """PUT /api/profile - updates profile"""
        # Get current profile
        current = auth_session.get(f"{BASE_URL}/api/profile").json()
        original_skill = current.get("skill_level", "beginner")
        
        # Update profile
        new_skill = "intermediate" if original_skill != "intermediate" else "advanced"
        payload = {"skill_level": new_skill}
        response = auth_session.put(f"{BASE_URL}/api/profile", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data["skill_level"] == new_skill, "Skill level should be updated"
        
        # Restore original
        auth_session.put(f"{BASE_URL}/api/profile", json={"skill_level": original_skill})
        print(f"✓ PUT /api/profile updates skill_level to: {new_skill}")
    
    def test_get_stats(self, auth_session):
        """GET /api/stats - returns dashboard stats"""
        response = auth_session.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "pantry_count" in data, "Response should contain pantry_count"
        assert "saved_recipes_count" in data, "Response should contain saved_recipes_count"
        assert "expiring_soon" in data, "Response should contain expiring_soon"
        assert "categories" in data, "Response should contain categories"
        print(f"✓ GET /api/stats - pantry: {data['pantry_count']}, recipes: {data['saved_recipes_count']}")
    
    def test_get_expiring_notifications(self, auth_session):
        """GET /api/notifications/expiring - returns expiry notifications"""
        response = auth_session.get(f"{BASE_URL}/api/notifications/expiring")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "notifications" in data, "Response should contain notifications"
        assert "count" in data, "Response should contain count"
        print(f"✓ GET /api/notifications/expiring - {data['count']} notifications")


# ========== MEAL PLAN TESTS ==========

class TestMealPlan:
    """Test meal plan endpoints"""
    
    def test_get_meal_plan(self, auth_session):
        """GET /api/mealplan - returns meal plan entries"""
        response = auth_session.get(f"{BASE_URL}/api/mealplan")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/mealplan returns {len(data)} entries")
    
    def test_add_meal_plan_entry(self, auth_session):
        """POST /api/mealplan - adds meal plan entry"""
        payload = {
            "day": "Monday",
            "meal_type": "breakfast",
            "recipe": {
                "title": f"TEST_Meal_{uuid.uuid4().hex[:6]}",
                "description": "Test breakfast"
            }
        }
        response = auth_session.post(f"{BASE_URL}/api/mealplan", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "entry_id" in data, "Response should contain entry_id"
        assert data["day"] == "Monday", "Day should match"
        assert data["meal_type"] == "breakfast", "Meal type should match"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/mealplan/{data['entry_id']}")
        print(f"✓ POST /api/mealplan adds entry: {data['recipe']['title']}")
    
    def test_delete_meal_plan_entry(self, auth_session):
        """DELETE /api/mealplan/{entry_id} - deletes entry"""
        # Create entry first
        payload = {
            "day": "Tuesday",
            "meal_type": "lunch",
            "recipe": {"title": f"TEST_Delete_{uuid.uuid4().hex[:6]}"}
        }
        create_response = auth_session.post(f"{BASE_URL}/api/mealplan", json=payload)
        assert create_response.status_code == 200
        entry_id = create_response.json()["entry_id"]
        
        # Delete entry
        delete_response = auth_session.delete(f"{BASE_URL}/api/mealplan/{entry_id}")
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}"
        data = delete_response.json()
        assert data.get("message") == "Deleted", "Should return deleted message"
        print(f"✓ DELETE /api/mealplan/{entry_id} removes entry")
    
    def test_clear_meal_plan(self, auth_session):
        """DELETE /api/mealplan - clears all entries"""
        # Add a test entry first
        payload = {
            "day": "Wednesday",
            "meal_type": "dinner",
            "recipe": {"title": f"TEST_Clear_{uuid.uuid4().hex[:6]}"}
        }
        auth_session.post(f"{BASE_URL}/api/mealplan", json=payload)
        
        # Clear meal plan
        response = auth_session.delete(f"{BASE_URL}/api/mealplan")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("message") == "Meal plan cleared", "Should return cleared message"
        
        # Verify cleared
        get_response = auth_session.get(f"{BASE_URL}/api/mealplan")
        assert len(get_response.json()) == 0, "Meal plan should be empty"
        print("✓ DELETE /api/mealplan clears all entries")


# ========== CART TESTS ==========

class TestCart:
    """Test cart endpoints"""
    
    def test_get_cart(self, auth_session):
        """GET /api/cart - returns cart"""
        response = auth_session.get(f"{BASE_URL}/api/cart")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "items" in data, "Response should contain items"
        assert "subtotal" in data, "Response should contain subtotal"
        assert "service_fee" in data, "Response should contain service_fee"
        assert "total" in data, "Response should contain total"
        print(f"✓ GET /api/cart - {data['item_count']} items, total: ${data['total']}")
    
    def test_add_to_cart(self, auth_session):
        """POST /api/cart/add - adds item to cart"""
        payload = {
            "name": f"TEST_Cart_{uuid.uuid4().hex[:6]}",
            "category": "dairy",
            "quantity": 1,
            "estimated_price": 3.99
        }
        response = auth_session.post(f"{BASE_URL}/api/cart/add", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "cart_item_id" in data, "Response should contain cart_item_id"
        assert data["name"] == payload["name"], "Name should match"
        assert data["estimated_price"] == 3.99, "Price should match"
        
        # Cleanup
        auth_session.delete(f"{BASE_URL}/api/cart/{data['cart_item_id']}")
        print(f"✓ POST /api/cart/add adds item: {data['name']}")
    
    def test_clear_cart(self, auth_session):
        """DELETE /api/cart - clears cart"""
        # Add test item first
        payload = {"name": f"TEST_Clear_{uuid.uuid4().hex[:6]}", "estimated_price": 1.99}
        auth_session.post(f"{BASE_URL}/api/cart/add", json=payload)
        
        # Clear cart
        response = auth_session.delete(f"{BASE_URL}/api/cart")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("message") == "Cart cleared", "Should return cleared message"
        
        # Verify cleared
        get_response = auth_session.get(f"{BASE_URL}/api/cart")
        assert get_response.json()["item_count"] == 0, "Cart should be empty"
        print("✓ DELETE /api/cart clears all items")


# ========== STORES TEST ==========

class TestStores:
    """Test stores endpoint"""
    
    def test_get_stores(self, auth_session):
        """GET /api/stores - returns list of stores"""
        response = auth_session.get(f"{BASE_URL}/api/stores")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "stores" in data, "Response should contain stores"
        assert isinstance(data["stores"], list), "Stores should be a list"
        assert len(data["stores"]) > 0, "Should have at least one store"
        
        store = data["stores"][0]
        assert "id" in store, "Store should have id"
        assert "name" in store, "Store should have name"
        assert "base_url" in store, "Store should have base_url"
        print(f"✓ GET /api/stores returns {len(data['stores'])} stores")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
