from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    allergies: List[str] = []
    dietary_preferences: List[str] = []
    skill_level: str = "beginner"
    default_servings: int = 2
    calorie_target: Optional[int] = None
    created_at: str = ""


class PantryItemCreate(BaseModel):
    name: str
    category: str = "other"
    quantity: Optional[str] = None
    unit: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None


class PantryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None


class RecipeGenerateRequest(BaseModel):
    ingredients: List[str] = []
    max_time: Optional[int] = None
    budget: Optional[str] = None
    skill_level: Optional[str] = None
    dietary_restrictions: List[str] = []
    servings: int = 2
    calorie_target: Optional[int] = None
    cuisine: Optional[str] = None
    meal_type: Optional[str] = None


class GroceryRequest(BaseModel):
    pantry_ingredients: List[str] = []
    preferences: List[str] = []
    budget: Optional[str] = None


class AuthRegister(BaseModel):
    email: str
    password: str
    name: str = "User"


class AuthLogin(BaseModel):
    email: str
    password: str


class MealPlanEntry(BaseModel):
    day: str
    meal_type: str
    recipe: dict
