import React from 'react';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { CookingPot, Scan, ShoppingCart, Leaf, ArrowRight } from '@phosphor-icons/react';

export default function Landing() {
  const { login } = useAuth();

  const features = [
    { icon: <CookingPot size={28} weight="duotone" />, title: "AI Recipe Generator", desc: "Turn your ingredients into delicious meals with AI-powered recipe creation" },
    { icon: <Scan size={28} weight="duotone" />, title: "Scan & Add", desc: "Snap a photo of your food or receipt to instantly add items to your pantry" },
    { icon: <ShoppingCart size={28} weight="duotone" />, title: "Smart Grocery List", desc: "Get personalized shopping suggestions based on what you have" },
    { icon: <Leaf size={28} weight="duotone" />, title: "Waste Nothing", desc: "Track expiry dates and get recipe ideas before food goes bad" },
  ];

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 sm:px-12 py-5">
        <div className="flex items-center gap-3">
          <img src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/bf1627652a4a5e009e74e84be99079dbe96eca13d294667f7cee5812cf142605.png" alt="Logo" className="w-10 h-10 rounded-xl" />
          <span className="font-heading font-bold text-xl text-[#2D3728]">Pantry Pulse</span>
        </div>
        <button
          data-testid="landing-login-btn"
          onClick={login}
          className="bg-[#2C5545] text-[#FDFBF7] rounded-full px-6 py-2.5 font-body font-medium hover:bg-[#3D6F5B] transition-colors text-sm"
        >
          Sign in with Google
        </button>
      </nav>

      {/* Hero */}
      <section className="px-6 sm:px-12 lg:px-20 pt-12 pb-20">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="inline-block bg-[#E8ECE1] text-[#2C5545] px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider mb-6">
              AI-Powered Cooking Assistant
            </span>
            <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl text-[#2D3728] tracking-tight leading-tight mb-6">
              Cook smarter<br />with what you<br /><span className="text-[#CC5500]">already have</span>
            </h1>
            <p className="text-[#5C6B54] text-base sm:text-lg leading-relaxed mb-8 max-w-lg font-body">
              Stop wasting food and money. Enter your ingredients, snap a photo, or scan a receipt and get personalized recipes tailored to your skill level, diet, and budget.
            </p>
            <button
              data-testid="hero-get-started-btn"
              onClick={login}
              className="bg-[#CC5500] text-white rounded-full px-8 py-3.5 font-body font-semibold hover:bg-[#E66000] transition-colors text-base inline-flex items-center gap-2 group"
            >
              Get Started Free
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
          >
            <img
              src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/10d58822537624b71e94058a90a133316d359dc6ea1ae5d9251ed0a0a1be36d7.png"
              alt="Fresh ingredients"
              className="w-full rounded-3xl shadow-[0_20px_60px_rgba(44,85,69,0.12)]"
            />
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 sm:px-12 lg:px-20 pb-24 bg-[#F4F1EA] py-20">
        <div className="max-w-7xl mx-auto">
          <h2 className="font-heading font-bold text-2xl sm:text-3xl lg:text-4xl text-[#2D3728] mb-12 tracking-tight">
            Everything you need to<br />cook with confidence
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="bg-white border border-[#E2E0D8] rounded-2xl p-6 hover:-translate-y-1 hover:shadow-[0_8px_24px_rgba(44,85,69,0.08)] transition-all duration-300"
              >
                <div className="w-12 h-12 bg-[#E8ECE1] rounded-xl flex items-center justify-center text-[#2C5545] mb-4">
                  {f.icon}
                </div>
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] mb-2">{f.title}</h3>
                <p className="text-[#5C6B54] text-sm leading-relaxed font-body">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Food Gallery */}
      <section className="px-6 sm:px-12 lg:px-20 py-20">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-6">
          <img src="https://images.pexels.com/photos/4198169/pexels-photo-4198169.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" alt="Fresh cooking" className="rounded-3xl w-full h-72 object-cover" />
          <img src="https://images.pexels.com/photos/4020559/pexels-photo-4020559.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" alt="Fresh vegetables" className="rounded-3xl w-full h-72 object-cover" />
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 sm:px-12 py-8 border-t border-[#E2E0D8]">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span className="text-sm text-[#5C6B54] font-body">Pantry Pulse</span>
          <span className="text-xs text-[#5C6B54] font-body">Powered by AI</span>
        </div>
      </footer>
    </div>
  );
}
