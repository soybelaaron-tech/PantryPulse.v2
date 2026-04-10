import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { ShoppingCart, Sparkle, Plus, CheckCircle, Tag } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function GroceryList() {
  const [pantryItems, setPantryItems] = useState([]);
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [checkedItems, setCheckedItems] = useState(new Set());

  useEffect(() => {
    const fetchPantry = async () => {
      try {
        const res = await axios.get(`${API}/pantry`, { withCredentials: true });
        setPantryItems(res.data);
      } catch (e) { console.error(e); }
    };
    fetchPantry();
  }, []);

  const generateSuggestions = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/grocery/suggestions`, {
        pantry_ingredients: pantryItems.map(i => i.name),
        preferences: [],
        budget: 'moderate'
      }, { withCredentials: true });
      setSuggestions(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to generate suggestions');
    } finally {
      setLoading(false);
    }
  };

  const toggleChecked = (name) => {
    const next = new Set(checkedItems);
    if (next.has(name)) next.delete(name);
    else next.add(name);
    setCheckedItems(next);
  };

  const addToPantry = async (item) => {
    try {
      await axios.post(`${API}/pantry`, {
        name: item.name,
        category: item.category || 'other',
      }, { withCredentials: true });
      toast.success(`${item.name} added to pantry`);
    } catch (e) {
      toast.error('Failed to add');
    }
  };

  const priorityColors = {
    high: 'bg-red-50 text-red-700 border-red-200',
    medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    low: 'bg-green-50 text-green-700 border-green-200',
  };

  const costIcons = { low: '$', medium: '$$', high: '$$$' };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight mb-1">
            <ShoppingCart size={28} weight="duotone" className="inline mr-2 text-[#2C5545]" />
            Smart Grocery List
          </h1>
          <p className="text-[#5C6B54] font-body text-sm mb-6">AI-powered suggestions based on your pantry</p>
        </motion.div>

        {/* Generate Button */}
        <button
          data-testid="generate-grocery-btn"
          onClick={generateSuggestions}
          disabled={loading}
          className="mb-8 bg-[#CC5500] text-white rounded-full px-8 py-3.5 font-body font-semibold hover:bg-[#E66000] transition-colors disabled:opacity-50 inline-flex items-center gap-2"
        >
          {loading ? (
            <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Analyzing pantry...</>
          ) : (
            <><Sparkle size={20} weight="fill" /> Generate Shopping List</>
          )}
        </button>

        {loading ? (
          <div className="flex flex-col items-center py-20">
            <div className="w-16 h-16 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-[#5C6B54] font-body">Analyzing your pantry and generating suggestions...</p>
          </div>
        ) : suggestions ? (
          <div className="space-y-6">
            {/* Meal Plan Preview */}
            {suggestions.meal_plan_preview && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-[#2C5545] rounded-3xl p-6 text-white">
                <h3 className="font-heading font-semibold text-lg mb-2">Meal Plan Preview</h3>
                <p className="text-white/80 font-body text-sm leading-relaxed">{suggestions.meal_plan_preview}</p>
              </motion.div>
            )}

            {/* Shopping Items */}
            <div className="space-y-3">
              {suggestions.suggestions?.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`bg-white border border-[#E2E0D8] rounded-2xl p-5 transition-all ${
                    checkedItems.has(item.name) ? 'opacity-60' : 'hover:shadow-[0_4px_16px_rgba(44,85,69,0.06)]'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <button
                      data-testid={`check-grocery-${i}`}
                      onClick={() => toggleChecked(item.name)}
                      className={`mt-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                        checkedItems.has(item.name) ? 'bg-[#2C5545] border-[#2C5545]' : 'border-[#E2E0D8]'
                      }`}
                    >
                      {checkedItems.has(item.name) && <CheckCircle size={16} weight="fill" className="text-white" />}
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className={`font-body font-medium text-[#2D3728] ${checkedItems.has(item.name) ? 'line-through' : ''}`}>{item.name}</h4>
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${priorityColors[item.priority] || priorityColors.medium}`}>
                          {item.priority}
                        </span>
                        <span className="text-xs text-[#5C6B54]">{costIcons[item.estimated_cost] || '$'}</span>
                      </div>
                      <p className="text-sm text-[#5C6B54] font-body">{item.reason}</p>
                      {item.recipes_enabled?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          <Tag size={14} className="text-[#2C5545]" />
                          {item.recipes_enabled.map(r => (
                            <span key={r} className="text-xs bg-[#E8ECE1] text-[#2C5545] px-2 py-0.5 rounded-full">{r}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    <button
                      data-testid={`add-grocery-to-pantry-${i}`}
                      onClick={() => addToPantry(item)}
                      className="flex-shrink-0 p-2 rounded-xl hover:bg-[#E8ECE1] text-[#2C5545] transition-colors"
                      title="Add to pantry"
                    >
                      <Plus size={18} weight="bold" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-20">
            <ShoppingCart size={64} weight="duotone" className="text-[#D5DCC9] mx-auto mb-4" />
            <p className="text-[#5C6B54] font-body mb-2">Your pantry has {pantryItems.length} items</p>
            <p className="text-[#5C6B54] font-body text-sm">Hit the button above to get smart grocery suggestions</p>
          </div>
        )}
      </main>
    </div>
  );
}
