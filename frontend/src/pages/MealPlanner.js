import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { CalendarBlank, Sparkle, Trash, Timer, Fire, ShoppingCart, CaretLeft, CaretRight, BookmarkSimple } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const MEAL_TYPES = ['breakfast', 'lunch', 'dinner'];
const MEAL_LABELS = { breakfast: 'Breakfast', lunch: 'Lunch', dinner: 'Dinner' };
const MEAL_COLORS = {
  breakfast: 'bg-amber-50 border-amber-200',
  lunch: 'bg-green-50 border-green-200',
  dinner: 'bg-blue-50 border-blue-200',
};

export default function MealPlanner() {
  const [mealPlan, setMealPlan] = useState([]);
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const [shoppingList, setShoppingList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [expandedMeal, setExpandedMeal] = useState(null);
  const [viewDay, setViewDay] = useState(0);

  useEffect(() => {
    fetchMealPlan();
  }, []);

  const fetchMealPlan = async () => {
    try {
      const res = await axios.get(`${API}/mealplan`, { withCredentials: true });
      setMealPlan(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const generatePlan = async () => {
    setGenerating(true);
    setGeneratedPlan(null);
    try {
      const res = await axios.post(`${API}/mealplan/generate`, { days: DAYS }, { withCredentials: true });
      setGeneratedPlan(res.data);
      setShoppingList(res.data.shopping_list || []);
      await fetchMealPlan();
      toast.success('Meal plan generated!');
    } catch (e) {
      console.error(e);
      toast.error('Failed to generate meal plan');
    } finally {
      setGenerating(false);
    }
  };

  const clearPlan = async () => {
    try {
      await axios.delete(`${API}/mealplan`, { withCredentials: true });
      setMealPlan([]);
      setGeneratedPlan(null);
      setShoppingList([]);
      toast.success('Meal plan cleared');
    } catch (e) { toast.error('Failed to clear'); }
  };

  const deleteMealEntry = async (entryId) => {
    try {
      await axios.delete(`${API}/mealplan/${entryId}`, { withCredentials: true });
      setMealPlan(mealPlan.filter(m => m.entry_id !== entryId));
      toast.success('Meal removed');
    } catch (e) { toast.error('Failed to remove'); }
  };

  const saveRecipe = async (recipe) => {
    try {
      await axios.post(`${API}/recipes/save`, { recipe }, { withCredentials: true });
      toast.success('Recipe saved to favorites!');
    } catch (e) { toast.error('Failed to save'); }
  };

  const getMealsForDay = (day) => {
    return mealPlan.filter(m => m.day === day);
  };

  const getMealForSlot = (day, mealType) => {
    return mealPlan.find(m => m.day === day && m.meal_type === mealType);
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight">
                <CalendarBlank size={28} weight="duotone" className="inline mr-2 text-[#2C5545]" />
                Meal Planner
              </h1>
              <p className="text-[#5C6B54] font-body text-sm mt-1">Plan your week with AI-powered meal suggestions</p>
            </div>
            <div className="flex gap-3">
              {mealPlan.length > 0 && (
                <button
                  data-testid="clear-meal-plan-btn"
                  onClick={clearPlan}
                  className="bg-white border border-[#E2E0D8] text-red-500 rounded-full px-5 py-2.5 font-body font-medium hover:bg-red-50 transition-colors text-sm inline-flex items-center gap-2"
                >
                  <Trash size={16} /> Clear Plan
                </button>
              )}
              <button
                data-testid="generate-meal-plan-btn"
                onClick={generatePlan}
                disabled={generating}
                className="bg-[#CC5500] text-white rounded-full px-6 py-2.5 font-body font-medium hover:bg-[#E66000] transition-colors text-sm inline-flex items-center gap-2 disabled:opacity-50"
              >
                {generating ? (
                  <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Generating...</>
                ) : (
                  <><Sparkle size={16} weight="fill" /> Generate Week</>
                )}
              </button>
            </div>
          </div>
        </motion.div>

        {generating ? (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="w-16 h-16 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-[#5C6B54] font-body text-lg">AI is crafting your weekly meal plan...</p>
            <p className="text-[#5C6B54] font-body text-sm mt-1">This may take a moment</p>
          </div>
        ) : loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : mealPlan.length === 0 ? (
          <div className="text-center py-20">
            <CalendarBlank size={64} weight="duotone" className="text-[#D5DCC9] mx-auto mb-4" />
            <p className="text-[#5C6B54] font-body text-lg mb-2">No meal plan yet</p>
            <p className="text-[#5C6B54] font-body text-sm mb-6">Generate an AI-powered weekly meal plan based on your pantry and preferences</p>
            <button
              data-testid="generate-meal-plan-empty-btn"
              onClick={generatePlan}
              className="bg-[#CC5500] text-white rounded-full px-8 py-3.5 font-body font-semibold hover:bg-[#E66000] transition-colors inline-flex items-center gap-2"
            >
              <Sparkle size={20} weight="fill" /> Generate My Meal Plan
            </button>
          </div>
        ) : (
          <>
            {/* Mobile day selector */}
            <div className="md:hidden flex items-center justify-between mb-4 bg-white border border-[#E2E0D8] rounded-2xl p-3">
              <button data-testid="prev-day-btn" onClick={() => setViewDay(Math.max(0, viewDay - 1))} disabled={viewDay === 0} className="p-2 rounded-xl hover:bg-[#F4F1EA] disabled:opacity-30">
                <CaretLeft size={20} />
              </button>
              <span className="font-heading font-semibold text-lg text-[#2D3728]">{DAYS[viewDay]}</span>
              <button data-testid="next-day-btn" onClick={() => setViewDay(Math.min(6, viewDay + 1))} disabled={viewDay === 6} className="p-2 rounded-xl hover:bg-[#F4F1EA] disabled:opacity-30">
                <CaretRight size={20} />
              </button>
            </div>

            {/* Desktop: Full week view */}
            <div className="hidden md:grid md:grid-cols-7 gap-3 mb-6">
              {DAYS.map((day, di) => {
                const dayMeals = getMealsForDay(day);
                return (
                  <motion.div
                    key={day}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: di * 0.05 }}
                    className="bg-white border border-[#E2E0D8] rounded-2xl overflow-hidden"
                  >
                    <div className="bg-[#2C5545] text-white px-3 py-2 text-center">
                      <p className="font-heading font-semibold text-sm">{day}</p>
                    </div>
                    <div className="p-2 space-y-2">
                      {MEAL_TYPES.map(mt => {
                        const meal = getMealForSlot(day, mt);
                        return (
                          <div
                            key={mt}
                            className={`rounded-xl p-2 border ${meal ? MEAL_COLORS[mt] : 'bg-[#F4F1EA] border-transparent'} cursor-pointer transition-all hover:shadow-sm`}
                            onClick={() => meal && setExpandedMeal(expandedMeal === meal.entry_id ? null : meal.entry_id)}
                          >
                            <p className="text-[10px] font-semibold uppercase tracking-wider text-[#5C6B54] mb-0.5">{MEAL_LABELS[mt]}</p>
                            {meal ? (
                              <>
                                <p className="text-xs font-medium text-[#2D3728] leading-snug line-clamp-2">{meal.recipe?.title}</p>
                                {meal.recipe?.total_time && (
                                  <p className="text-[10px] text-[#5C6B54] mt-0.5 flex items-center gap-0.5">
                                    <Timer size={10} /> {meal.recipe.total_time}m
                                  </p>
                                )}
                              </>
                            ) : (
                              <p className="text-[10px] text-[#5C6B54]">-</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {/* Mobile: Single day view */}
            <div className="md:hidden space-y-3 mb-6">
              {MEAL_TYPES.map(mt => {
                const meal = getMealForSlot(DAYS[viewDay], mt);
                return (
                  <div key={mt} className={`rounded-2xl p-4 border ${meal ? MEAL_COLORS[mt] : 'bg-[#F4F1EA] border-transparent'}`}>
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#5C6B54] mb-1">{MEAL_LABELS[mt]}</p>
                    {meal ? (
                      <>
                        <p className="font-body font-medium text-[#2D3728]">{meal.recipe?.title}</p>
                        <p className="text-sm text-[#5C6B54] mt-1">{meal.recipe?.description}</p>
                        <div className="flex gap-2 mt-2">
                          {meal.recipe?.total_time && <span className="text-xs bg-white/70 px-2 py-1 rounded-full inline-flex items-center gap-1"><Timer size={12} /> {meal.recipe.total_time}m</span>}
                          {meal.recipe?.calories_per_serving && <span className="text-xs bg-white/70 px-2 py-1 rounded-full inline-flex items-center gap-1"><Fire size={12} /> {meal.recipe.calories_per_serving} cal</span>}
                        </div>
                        <div className="flex gap-2 mt-3">
                          <button onClick={() => setExpandedMeal(expandedMeal === meal.entry_id ? null : meal.entry_id)} className="text-[#2C5545] text-xs font-medium hover:underline">
                            {expandedMeal === meal.entry_id ? 'Hide' : 'View Recipe'}
                          </button>
                          <button onClick={() => deleteMealEntry(meal.entry_id)} className="text-red-500 text-xs font-medium hover:underline">Remove</button>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-[#5C6B54]">No meal planned</p>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Expanded meal detail */}
            {expandedMeal && (() => {
              const meal = mealPlan.find(m => m.entry_id === expandedMeal);
              if (!meal) return null;
              const recipe = meal.recipe;
              return (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_8px_24px_rgba(44,85,69,0.08)] mb-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="text-xs text-[#5C6B54] font-semibold uppercase tracking-wider">{meal.day} - {MEAL_LABELS[meal.meal_type]}</p>
                      <h3 className="font-heading font-bold text-xl text-[#2D3728] mt-1">{recipe?.title}</h3>
                      <p className="text-[#5C6B54] text-sm font-body mt-1">{recipe?.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <button data-testid={`save-meal-recipe-${meal.entry_id}`} onClick={() => saveRecipe(recipe)} className="p-2 rounded-xl hover:bg-[#E8ECE1] text-[#2C5545]">
                        <BookmarkSimple size={20} weight="duotone" />
                      </button>
                      <button data-testid={`delete-meal-${meal.entry_id}`} onClick={() => { deleteMealEntry(meal.entry_id); setExpandedMeal(null); }} className="p-2 rounded-xl hover:bg-red-50 text-red-500">
                        <Trash size={20} />
                      </button>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {recipe?.total_time && <span className="text-xs bg-[#F4F1EA] px-3 py-1.5 rounded-full inline-flex items-center gap-1"><Timer size={14} /> {recipe.total_time} min</span>}
                    {recipe?.calories_per_serving && <span className="text-xs bg-[#F4F1EA] px-3 py-1.5 rounded-full inline-flex items-center gap-1"><Fire size={14} /> {recipe.calories_per_serving} cal</span>}
                  </div>
                  {recipe?.ingredients_used?.length > 0 && (
                    <div className="mb-3">
                      <h4 className="text-sm font-semibold text-[#2D3728] mb-1.5 font-heading">From Your Pantry</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {recipe.ingredients_used.map(ing => <span key={ing} className="text-xs bg-[#E8ECE1] text-[#2C5545] px-2.5 py-1 rounded-full">{ing}</span>)}
                      </div>
                    </div>
                  )}
                  {recipe?.ingredients_needed?.length > 0 && (
                    <div className="mb-3">
                      <h4 className="text-sm font-semibold text-[#CC5500] mb-1.5 font-heading">Need to Buy</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {recipe.ingredients_needed.map(ing => <span key={ing} className="text-xs bg-orange-50 text-orange-700 px-2.5 py-1 rounded-full border border-orange-200">{ing}</span>)}
                      </div>
                    </div>
                  )}
                  {recipe?.instructions?.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-semibold text-[#2D3728] mb-2 font-heading">Instructions</h4>
                      <ol className="space-y-2">
                        {recipe.instructions.map((step, si) => (
                          <li key={si} className="flex gap-3 text-sm text-[#2D3728] font-body">
                            <span className="flex-shrink-0 w-6 h-6 bg-[#2C5545] text-white rounded-full flex items-center justify-center text-xs font-bold">{si + 1}</span>
                            <span className="pt-0.5 leading-relaxed">{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </motion.div>
              );
            })()}

            {/* Shopping List */}
            {shoppingList.length > 0 && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] mb-3">
                  <ShoppingCart size={20} weight="duotone" className="inline mr-2 text-[#CC5500]" />
                  Shopping List for This Plan
                </h3>
                <div className="flex flex-wrap gap-2">
                  {shoppingList.map((item, i) => (
                    <span key={i} className="text-sm bg-orange-50 text-orange-700 px-3 py-1.5 rounded-full border border-orange-200">{item}</span>
                  ))}
                </div>
              </motion.div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
