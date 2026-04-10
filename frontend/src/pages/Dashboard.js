import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion } from 'framer-motion';
import { CookingPot, Package, ShoppingCart, Camera, Warning, ArrowRight, Plus } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get(`${API}/stats`, { withCredentials: true });
        setStats(res.data);
      } catch (e) {
        console.error('Stats fetch error:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const quickActions = [
    { icon: <CookingPot size={24} weight="duotone" />, label: "Generate Recipes", path: "/recipes", color: "bg-[#2C5545] text-white" },
    { icon: <Plus size={24} weight="bold" />, label: "Add Ingredients", path: "/pantry", color: "bg-[#CC5500] text-white" },
    { icon: <Camera size={24} weight="duotone" />, label: "Scan Items", path: "/scan", color: "bg-[#E8ECE1] text-[#2C5545]" },
    { icon: <ShoppingCart size={24} weight="duotone" />, label: "Grocery List", path: "/grocery", color: "bg-[#E8ECE1] text-[#2C5545]" },
  ];

  const categories = stats?.categories || {};
  const categoryLabels = {
    protein: "Protein", dairy: "Dairy", vegetable: "Vegetables", fruit: "Fruits",
    grain: "Grains", spice: "Spices", condiment: "Condiments", other: "Other"
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-7xl mx-auto">
        {/* Greeting */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 data-testid="dashboard-greeting" className="font-heading font-bold text-3xl sm:text-4xl text-[#2D3728] tracking-tight">
            Hey, {user?.name?.split(' ')[0] || 'Chef'}
          </h1>
          <p className="text-[#5C6B54] mt-1 font-body">What are we cooking today?</p>
        </motion.div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {quickActions.map((action, i) => (
            <motion.button
              key={action.label}
              data-testid={`quick-action-${action.label.toLowerCase().replace(/\s/g, '-')}`}
              onClick={() => navigate(action.path)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`${action.color} rounded-2xl p-5 flex flex-col items-start gap-3 hover:-translate-y-1 hover:shadow-lg transition-all duration-300`}
            >
              {action.icon}
              <span className="font-body font-medium text-sm">{action.label}</span>
            </motion.button>
          ))}
        </div>

        {/* Bento Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* Pantry Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)] md:col-span-2"
          >
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-heading font-semibold text-xl text-[#2D3728]">
                <Package size={22} weight="duotone" className="inline mr-2 text-[#2C5545]" />
                Your Pantry
              </h2>
              <button
                data-testid="view-pantry-btn"
                onClick={() => navigate('/pantry')}
                className="text-[#2C5545] text-sm font-medium flex items-center gap-1 hover:gap-2 transition-all"
              >
                View all <ArrowRight size={16} />
              </button>
            </div>
            {loading ? (
              <div className="h-32 flex items-center justify-center">
                <div className="w-8 h-8 border-3 border-[#2C5545] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : stats?.pantry_count === 0 ? (
              <div className="text-center py-8">
                <img src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/f4e62cb7650b50067854b3bd5d01361e8015e4a5d18df085abc4ab7ae4546321.png" alt="Empty pantry" className="w-36 mx-auto mb-4 opacity-70" />
                <p className="text-[#5C6B54] text-sm font-body">Your pantry is empty. Start adding ingredients!</p>
                <button onClick={() => navigate('/pantry')} className="mt-3 text-[#CC5500] font-medium text-sm">Add items</button>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(categories).map(([cat, count]) => (
                  <div key={cat} className="bg-[#F4F1EA] rounded-xl p-3 text-center">
                    <p className="font-heading font-bold text-2xl text-[#2C5545]">{count}</p>
                    <p className="text-[#5C6B54] text-xs capitalize font-body">{categoryLabels[cat] || cat}</p>
                  </div>
                ))}
                <div className="bg-[#E8ECE1] rounded-xl p-3 text-center">
                  <p className="font-heading font-bold text-2xl text-[#2C5545]">{stats?.pantry_count || 0}</p>
                  <p className="text-[#5C6B54] text-xs font-body">Total Items</p>
                </div>
              </div>
            )}
          </motion.div>

          {/* Expiring Soon */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]"
          >
            <h2 className="font-heading font-semibold text-xl text-[#2D3728] mb-4">
              <Warning size={22} weight="duotone" className="inline mr-2 text-[#CC5500]" />
              Expiring Soon
            </h2>
            {loading ? (
              <div className="h-20 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-[#CC5500] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : !stats?.expiring_soon?.length ? (
              <p className="text-[#5C6B54] text-sm font-body py-4">No items expiring soon. Nice!</p>
            ) : (
              <div className="space-y-3">
                {stats.expiring_soon.slice(0, 5).map((item) => (
                  <div key={item.item_id} className="flex items-center justify-between py-2 border-b border-[#F4F1EA] last:border-0">
                    <span className="text-sm font-medium text-[#2D3728] font-body">{item.name}</span>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      item.days_left <= 1 ? 'bg-red-50 text-red-600' : 'bg-orange-50 text-orange-600'
                    }`}>
                      {item.days_left === 0 ? 'Today' : `${item.days_left}d left`}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>

          {/* Saved Recipes Count */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-[#2C5545] rounded-3xl p-6 text-white cursor-pointer hover:-translate-y-1 transition-all duration-300"
            onClick={() => navigate('/saved')}
          >
            <CookingPot size={32} weight="duotone" className="mb-3 opacity-80" />
            <p className="font-heading font-bold text-4xl">{stats?.saved_recipes_count || 0}</p>
            <p className="text-white/70 text-sm font-body mt-1">Saved Recipes</p>
          </motion.div>

          {/* Scan CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)] md:col-span-2 flex items-center gap-6 cursor-pointer hover:-translate-y-1 hover:shadow-lg transition-all duration-300"
            onClick={() => navigate('/scan')}
          >
            <img
              src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/1a8a3c53284c1ac05fa457b62feb443d373fc1f5c9129f8066e0fc9b632db36d.png"
              alt="Scan receipt"
              className="w-24 h-24 rounded-2xl object-cover flex-shrink-0"
            />
            <div>
              <h3 className="font-heading font-semibold text-lg text-[#2D3728]">Scan a Receipt or Food Photo</h3>
              <p className="text-[#5C6B54] text-sm font-body mt-1">Use AI to instantly identify and add ingredients to your pantry</p>
            </div>
            <ArrowRight size={24} className="text-[#2C5545] ml-auto flex-shrink-0" />
          </motion.div>
        </div>
      </main>
    </div>
  );
}
