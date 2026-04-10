import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { BookmarkSimple, Trash, Timer, Users, Fire } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SavedRecipes() {
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get(`${API}/recipes/saved`, { withCredentials: true });
        setRecipes(res.data);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    fetch();
  }, []);

  const deleteRecipe = async (savedId) => {
    try {
      await axios.delete(`${API}/recipes/saved/${savedId}`, { withCredentials: true });
      setRecipes(recipes.filter(r => r.saved_id !== savedId));
    } catch (e) { console.error(e); }
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight mb-1">
            <BookmarkSimple size={28} weight="duotone" className="inline mr-2 text-[#2C5545]" />
            Saved Recipes
          </h1>
          <p className="text-[#5C6B54] font-body text-sm mb-6">{recipes.length} recipes saved</p>
        </motion.div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : recipes.length === 0 ? (
          <div className="text-center py-20">
            <BookmarkSimple size={64} weight="duotone" className="text-[#D5DCC9] mx-auto mb-4" />
            <p className="text-[#5C6B54] font-body">No saved recipes yet. Generate some and save your favorites!</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            <AnimatePresence>
              {recipes.map((recipe, i) => (
                <motion.div
                  key={recipe.saved_id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)] hover:shadow-[0_8px_24px_rgba(44,85,69,0.08)] transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="font-heading font-bold text-lg text-[#2D3728]">{recipe.title}</h3>
                    <button
                      data-testid={`delete-saved-${recipe.saved_id}`}
                      onClick={() => deleteRecipe(recipe.saved_id)}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-red-500"
                    >
                      <Trash size={18} />
                    </button>
                  </div>
                  <p className="text-[#5C6B54] text-sm font-body mb-3">{recipe.description}</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="inline-flex items-center gap-1 text-xs bg-[#F4F1EA] text-[#2D3728] px-2.5 py-1 rounded-full">
                      <Timer size={12} /> {recipe.total_time || '?'} min
                    </span>
                    <span className="inline-flex items-center gap-1 text-xs bg-[#F4F1EA] text-[#2D3728] px-2.5 py-1 rounded-full">
                      <Users size={12} /> {recipe.servings}
                    </span>
                    <span className="inline-flex items-center gap-1 text-xs bg-[#F4F1EA] text-[#2D3728] px-2.5 py-1 rounded-full">
                      <Fire size={12} /> {recipe.calories_per_serving || '?'} cal
                    </span>
                  </div>
                  <button
                    data-testid={`toggle-saved-instructions-${recipe.saved_id}`}
                    onClick={() => setExpanded(expanded === recipe.saved_id ? null : recipe.saved_id)}
                    className="text-[#2C5545] text-sm font-medium hover:underline"
                  >
                    {expanded === recipe.saved_id ? 'Hide' : 'View Instructions'}
                  </button>
                  {expanded === recipe.saved_id && (
                    <motion.ol initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 space-y-2">
                      {recipe.instructions?.map((step, si) => (
                        <li key={si} className="flex gap-2 text-sm text-[#2D3728] font-body">
                          <span className="font-bold text-[#2C5545]">{si + 1}.</span> {step}
                        </li>
                      ))}
                    </motion.ol>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </main>
    </div>
  );
}
