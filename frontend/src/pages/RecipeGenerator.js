import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { CookingPot, Timer, Fire, Users, Sparkle, X, Plus, BookmarkSimple, FunnelSimple, Knife } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Slider } from '../components/ui/slider';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DIETARY_OPTIONS = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Keto', 'Paleo', 'Nut-Free', 'Low-Carb', 'Halal', 'Kosher'];
const CUISINE_OPTIONS = ['Any', 'Italian', 'Mexican', 'Chinese', 'Japanese', 'Indian', 'Thai', 'Mediterranean', 'American', 'French', 'Korean'];
const MEAL_TYPES = ['Any', 'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Dessert'];

const COMMON_INGREDIENTS = {
  'Proteins': ['Chicken Breast', 'Ground Beef', 'Salmon', 'Shrimp', 'Tofu', 'Eggs', 'Bacon', 'Sausage', 'Turkey', 'Tuna', 'Pork Chops', 'Steak'],
  'Vegetables': ['Onion', 'Garlic', 'Tomato', 'Bell Pepper', 'Broccoli', 'Spinach', 'Carrot', 'Potato', 'Mushroom', 'Zucchini', 'Corn', 'Green Beans', 'Avocado', 'Lettuce', 'Celery', 'Cucumber'],
  'Fruits': ['Lemon', 'Lime', 'Banana', 'Apple', 'Strawberry', 'Blueberry', 'Orange', 'Mango'],
  'Dairy': ['Butter', 'Milk', 'Cheese', 'Cream Cheese', 'Sour Cream', 'Yogurt', 'Parmesan', 'Mozzarella', 'Heavy Cream'],
  'Grains & Carbs': ['Rice', 'Pasta', 'Bread', 'Tortilla', 'Ramen Noodles', 'Quinoa', 'Oats', 'Flour'],
  'Pantry Staples': ['Olive Oil', 'Soy Sauce', 'Salt', 'Pepper', 'Sugar', 'Vinegar', 'Ketchup', 'Mustard', 'Hot Sauce', 'Honey', 'Peanut Butter', 'Coconut Milk', 'Chicken Broth', 'Tomato Sauce', 'Canned Beans'],
  'Spices': ['Paprika', 'Cumin', 'Oregano', 'Chili Powder', 'Cinnamon', 'Ginger', 'Turmeric', 'Basil', 'Thyme', 'Red Pepper Flakes', 'Garlic Powder', 'Onion Powder'],
};

export default function RecipeGenerator() {
  const [ingredients, setIngredients] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [pantryItems, setPantryItems] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedRecipe, setExpandedRecipe] = useState(null);
  const [cookedRecipes, setCookedRecipes] = useState(new Set());

  const [showFilters, setShowFilters] = useState(false);
  const [maxTime, setMaxTime] = useState([60]);
  const [budget, setBudget] = useState('moderate');
  const [skillLevel, setSkillLevel] = useState('beginner');
  const [servings, setServings] = useState([2]);
  const [calorieTarget, setCalorieTarget] = useState([0]);
  const [dietary, setDietary] = useState([]);
  const [cuisine, setCuisine] = useState('Any');
  const [mealType, setMealType] = useState('Any');
  const [expandedCategory, setExpandedCategory] = useState(null);

  useEffect(() => {
    const fetchPantry = async () => {
      try {
        const res = await axios.get(`${API}/pantry`, { withCredentials: true });
        setPantryItems(res.data);
      } catch (e) { console.error(e); }
    };
    fetchPantry();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const addIngredient = (name) => {
    const trimmed = name.trim();
    if (trimmed && !ingredients.includes(trimmed)) {
      setIngredients([...ingredients, trimmed]);
    }
    setInputVal('');
  };

  const removeIngredient = (ing) => {
    setIngredients(ingredients.filter(i => i !== ing));
  };

  const toggleDietary = (d) => {
    setDietary(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]);
  };

  const generateRecipes = async () => {
    if (ingredients.length === 0) {
      toast.error('Add at least one ingredient');
      return;
    }
    setLoading(true);
    setRecipes([]);
    try {
      const payload = {
        ingredients,
        max_time: maxTime[0] || null,
        budget,
        skill_level: skillLevel,
        dietary_restrictions: dietary,
        servings: servings[0],
        calorie_target: calorieTarget[0] > 0 ? calorieTarget[0] : null,
        cuisine: cuisine !== 'Any' ? cuisine : null,
        meal_type: mealType !== 'Any' ? mealType : null,
      };
      const res = await axios.post(`${API}/recipes/generate`, payload, { withCredentials: true });
      setRecipes(res.data.recipes || []);
    } catch (e) {
      console.error(e);
      toast.error('Failed to generate recipes. Try again!');
    } finally {
      setLoading(false);
    }
  };

  const saveRecipe = async (recipe) => {
    try {
      await axios.post(`${API}/recipes/save`, { recipe }, { withCredentials: true });
      toast.success('Recipe saved!');
    } catch (e) {
      toast.error('Failed to save recipe');
    }
  };

  const cookRecipe = async (recipe) => {
    const usedIngredients = recipe.ingredients_used || [];
    if (usedIngredients.length === 0) {
      toast.info('No pantry ingredients to deduct');
      return;
    }
    try {
      const res = await axios.post(`${API}/recipes/cook`, { ingredients_used: usedIngredients }, { withCredentials: true });
      const { removed, not_found } = res.data;
      setCookedRecipes(new Set([...cookedRecipes, recipe.recipe_id]));
      if (removed.length > 0) {
        toast.success(`Cooking! Removed ${removed.length} ingredient${removed.length > 1 ? 's' : ''} from pantry`);
      }
      if (not_found.length > 0) {
        toast.info(`${not_found.length} ingredient${not_found.length > 1 ? 's were' : ' was'} not in your pantry`);
      }
    } catch (e) {
      toast.error('Failed to update pantry');
    }
  };

  const useFromPantry = () => {
    const names = pantryItems.map(i => i.name);
    setIngredients([...new Set([...ingredients, ...names])]);
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight mb-1">Recipe Generator</h1>
          <p className="text-[#5C6B54] font-body text-sm mb-6">Enter your ingredients and let AI create delicious recipes for you</p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left: Ingredients + Filters */}
          <div className="lg:col-span-1 space-y-6">
            {/* Ingredient Input */}
            <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
              <h2 className="font-heading font-semibold text-lg text-[#2D3728] mb-3">Ingredients</h2>
              <div className="flex gap-2 mb-3">
                <input
                  data-testid="ingredient-input"
                  value={inputVal}
                  onChange={e => setInputVal(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') addIngredient(inputVal); }}
                  placeholder="Type an ingredient..."
                  className="flex-1 bg-white border border-[#E2E0D8] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                />
                <button
                  data-testid="add-ingredient-btn"
                  onClick={() => addIngredient(inputVal)}
                  className="bg-[#2C5545] text-white rounded-xl px-3 py-2.5 hover:bg-[#3D6F5B] transition-colors"
                >
                  <Plus size={18} weight="bold" />
                </button>
              </div>
              {pantryItems.length > 0 && (
                <button
                  data-testid="use-pantry-btn"
                  onClick={useFromPantry}
                  className="text-[#CC5500] text-xs font-medium mb-3 hover:underline"
                >
                  + Add all from pantry ({pantryItems.length} items)
                </button>
              )}

              {/* Selected ingredients */}
              <div className="flex flex-wrap gap-2 mb-4">
                {ingredients.map(ing => (
                  <span key={ing} className="inline-flex items-center gap-1 bg-[#E8ECE1] text-[#2C5545] px-3 py-1.5 rounded-full text-xs font-medium">
                    {ing}
                    <button onClick={() => removeIngredient(ing)} className="hover:text-red-500">
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>

              {/* Common Ingredients Quick-Select */}
              <div className="border-t border-[#F4F1EA] pt-3">
                <p className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2">Quick Add</p>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {Object.keys(COMMON_INGREDIENTS).map(cat => (
                    <button
                      key={cat}
                      data-testid={`ingredient-cat-${cat.toLowerCase().replace(/[\s&]/g, '-')}`}
                      onClick={() => setExpandedCategory(expandedCategory === cat ? null : cat)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                        expandedCategory === cat
                          ? 'bg-[#2C5545] text-white border-[#2C5545]'
                          : 'bg-white text-[#5C6B54] border-[#E2E0D8] hover:border-[#2C5545]'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
                {expandedCategory && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="flex flex-wrap gap-1.5 mt-2">
                    {COMMON_INGREDIENTS[expandedCategory].map(ing => {
                      const isSelected = ingredients.includes(ing);
                      return (
                        <button
                          key={ing}
                          data-testid={`quick-ing-${ing.toLowerCase().replace(/\s/g, '-')}`}
                          onClick={() => { if (!isSelected) addIngredient(ing); else removeIngredient(ing); }}
                          className={`text-xs px-2.5 py-1.5 rounded-full border transition-all ${
                            isSelected
                              ? 'bg-[#2C5545] text-white border-[#2C5545]'
                              : 'bg-[#F4F1EA] text-[#2D3728] border-transparent hover:bg-[#E8ECE1]'
                          }`}
                        >
                          {isSelected ? '✓ ' : '+ '}{ing}
                        </button>
                      );
                    })}
                  </motion.div>
                )}
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
              <button data-testid="toggle-filters-btn" onClick={() => setShowFilters(!showFilters)} className="flex items-center justify-between w-full">
                <h2 className="font-heading font-semibold text-lg text-[#2D3728]">
                  <FunnelSimple size={20} weight="duotone" className="inline mr-2" />Filters
                </h2>
                <span className="text-xs text-[#5C6B54]">{showFilters ? 'Hide' : 'Show'}</span>
              </button>
              {showFilters && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-4 space-y-4">
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Max Cook Time: {maxTime[0]} min</label>
                    <Slider data-testid="time-slider" value={maxTime} onValueChange={setMaxTime} max={120} step={5} className="mt-1" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Servings: {servings[0]}</label>
                    <Slider data-testid="servings-slider" value={servings} onValueChange={setServings} min={1} max={12} step={1} className="mt-1" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Calories/Serving: {calorieTarget[0] === 0 ? 'Any' : calorieTarget[0]}</label>
                    <Slider data-testid="calories-slider" value={calorieTarget} onValueChange={setCalorieTarget} max={2000} step={50} className="mt-1" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Budget</label>
                    <Select value={budget} onValueChange={setBudget}>
                      <SelectTrigger data-testid="budget-select" className="rounded-xl border-[#E2E0D8]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Budget-Friendly</SelectItem>
                        <SelectItem value="moderate">Moderate</SelectItem>
                        <SelectItem value="high">No Limit</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Skill Level</label>
                    <Select value={skillLevel} onValueChange={setSkillLevel}>
                      <SelectTrigger data-testid="skill-select" className="rounded-xl border-[#E2E0D8]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="beginner">Beginner</SelectItem>
                        <SelectItem value="intermediate">Intermediate</SelectItem>
                        <SelectItem value="advanced">Advanced</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Cuisine</label>
                    <Select value={cuisine} onValueChange={setCuisine}>
                      <SelectTrigger data-testid="cuisine-select" className="rounded-xl border-[#E2E0D8]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {CUISINE_OPTIONS.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Meal Type</label>
                    <Select value={mealType} onValueChange={setMealType}>
                      <SelectTrigger data-testid="meal-type-select" className="rounded-xl border-[#E2E0D8]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {MEAL_TYPES.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Dietary</label>
                    <div className="flex flex-wrap gap-2">
                      {DIETARY_OPTIONS.map(d => (
                        <button
                          key={d}
                          data-testid={`dietary-${d.toLowerCase()}`}
                          onClick={() => toggleDietary(d)}
                          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                            dietary.includes(d) ? 'bg-[#2C5545] text-white border-[#2C5545]' : 'bg-white text-[#5C6B54] border-[#E2E0D8] hover:border-[#2C5545]'
                          }`}
                        >
                          {d}
                        </button>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            <button
              data-testid="generate-recipes-btn"
              onClick={generateRecipes}
              disabled={loading || ingredients.length === 0}
              className="w-full bg-[#CC5500] text-white rounded-full py-3.5 font-body font-semibold hover:bg-[#E66000] transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
            >
              {loading ? (
                <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Generating...</>
              ) : (
                <><Sparkle size={20} weight="fill" /> Generate Recipes</>
              )}
            </button>
          </div>

          {/* Right: Results */}
          <div className="lg:col-span-2">
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20">
                <div className="w-16 h-16 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-[#5C6B54] font-body">Our AI chef is cooking up recipes...</p>
              </div>
            ) : recipes.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <CookingPot size={64} weight="duotone" className="text-[#D5DCC9] mb-4" />
                <p className="text-[#5C6B54] font-body">Add ingredients and hit generate to see recipe magic!</p>
              </div>
            ) : (
              <div className="space-y-6">
                {recipes.map((recipe, i) => (
                  <motion.div
                    key={recipe.recipe_id || i}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)] hover:shadow-[0_8px_24px_rgba(44,85,69,0.08)] transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-heading font-bold text-xl text-[#2D3728]">{recipe.title}</h3>
                        <p className="text-[#5C6B54] text-sm font-body mt-1">{recipe.description}</p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          data-testid={`cook-recipe-${i}`}
                          onClick={() => cookRecipe(recipe)}
                          disabled={cookedRecipes.has(recipe.recipe_id)}
                          className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors inline-flex items-center gap-1.5 ${
                            cookedRecipes.has(recipe.recipe_id)
                              ? 'bg-green-50 text-green-700'
                              : 'bg-[#CC5500] text-white hover:bg-[#E66000]'
                          }`}
                        >
                          {cookedRecipes.has(recipe.recipe_id) ? (
                            <><Knife size={16} /> Cooked!</>
                          ) : (
                            <><Knife size={16} /> Cook This</>
                          )}
                        </button>
                        <button
                          data-testid={`save-recipe-${i}`}
                          onClick={() => saveRecipe(recipe)}
                          className="p-2 rounded-xl hover:bg-[#E8ECE1] text-[#2C5545] transition-colors"
                        >
                          <BookmarkSimple size={22} weight="duotone" />
                        </button>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-3 mb-4">
                      <span className="inline-flex items-center gap-1 text-xs bg-[#F4F1EA] text-[#2D3728] px-3 py-1.5 rounded-full">
                        <Timer size={14} /> {recipe.total_time || '?'} min
                      </span>
                      <span className="inline-flex items-center gap-1 text-xs bg-[#F4F1EA] text-[#2D3728] px-3 py-1.5 rounded-full">
                        <Users size={14} /> {recipe.servings} servings
                      </span>
                      <span className="inline-flex items-center gap-1 text-xs bg-[#F4F1EA] text-[#2D3728] px-3 py-1.5 rounded-full">
                        <Fire size={14} /> {recipe.calories_per_serving || '?'} cal
                      </span>
                      <span className={`text-xs px-3 py-1.5 rounded-full capitalize ${
                        recipe.difficulty === 'easy' ? 'bg-green-50 text-green-700' :
                        recipe.difficulty === 'medium' ? 'bg-yellow-50 text-yellow-700' :
                        'bg-red-50 text-red-700'
                      }`}>{recipe.difficulty}</span>
                      {recipe.tags?.map(tag => (
                        <span key={tag} className="text-xs bg-[#E8ECE1] text-[#2C5545] px-3 py-1.5 rounded-full">{tag}</span>
                      ))}
                    </div>

                    {/* Ingredients */}
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-[#2D3728] mb-2 font-heading">Ingredients You Have</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {recipe.ingredients_used?.map(ing => (
                          <span key={ing} className="text-xs bg-[#E8ECE1] text-[#2C5545] px-2.5 py-1 rounded-full">{ing}</span>
                        ))}
                      </div>
                      {recipe.ingredients_needed?.length > 0 && (
                        <>
                          <h4 className="text-sm font-semibold text-[#CC5500] mt-3 mb-2 font-heading">You'll Need</h4>
                          <div className="flex flex-wrap gap-1.5">
                            {recipe.ingredients_needed.map(ing => (
                              <span key={ing} className="text-xs bg-orange-50 text-orange-700 px-2.5 py-1 rounded-full border border-orange-200">{ing}</span>
                            ))}
                          </div>
                        </>
                      )}
                    </div>

                    {/* Toggle instructions */}
                    <button
                      data-testid={`toggle-instructions-${i}`}
                      onClick={() => setExpandedRecipe(expandedRecipe === i ? null : i)}
                      className="text-[#2C5545] text-sm font-medium hover:underline"
                    >
                      {expandedRecipe === i ? 'Hide Instructions' : 'Show Instructions'}
                    </button>

                    {expandedRecipe === i && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-4">
                        <ol className="space-y-3">
                          {recipe.instructions?.map((step, si) => (
                            <li key={si} className="flex gap-3">
                              <span className="flex-shrink-0 w-7 h-7 bg-[#2C5545] text-white rounded-full flex items-center justify-center text-xs font-bold">{si + 1}</span>
                              <p className="text-sm text-[#2D3728] font-body leading-relaxed pt-0.5">{step}</p>
                            </li>
                          ))}
                        </ol>
                        {recipe.tips && (
                          <div className="mt-4 bg-[#F4F1EA] rounded-xl p-4">
                            <p className="text-sm text-[#2C5545] font-body"><strong>Tip:</strong> {recipe.tips}</p>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
