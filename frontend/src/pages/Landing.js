import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { CookingPot, Scan, ShoppingCart, Leaf, ArrowRight, Envelope, Lock, User, GoogleLogo, Eye, EyeSlash } from '@phosphor-icons/react';

export default function Landing() {
  const { loginWithGoogle, loginWithEmail, register, formatApiError } = useAuth();
  const navigate = useNavigate();
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      if (authMode === 'login') {
        await loginWithEmail(email, password);
      } else {
        await register(email, password, name);
      }
      navigate('/dashboard');
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setSubmitting(false);
    }
  };

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
          onClick={() => setShowAuth(true)}
          className="bg-[#2C5545] text-[#FDFBF7] rounded-full px-6 py-2.5 font-body font-medium hover:bg-[#3D6F5B] transition-colors text-sm"
        >
          Sign In
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
              onClick={() => setShowAuth(true)}
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

      {/* Auth Modal */}
      <AnimatePresence>
        {showAuth && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4"
            onClick={() => setShowAuth(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.25 }}
              className="bg-white rounded-3xl w-full max-w-md p-8 shadow-[0_24px_64px_rgba(0,0,0,0.15)] relative"
              onClick={e => e.stopPropagation()}
            >
              <button
                data-testid="close-auth-modal"
                onClick={() => setShowAuth(false)}
                className="absolute top-4 right-4 text-[#5C6B54] hover:text-[#2D3728] transition-colors"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M15 5L5 15M5 5l10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
              </button>

              <div className="text-center mb-6">
                <img src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/bf1627652a4a5e009e74e84be99079dbe96eca13d294667f7cee5812cf142605.png" alt="Logo" className="w-12 h-12 rounded-xl mx-auto mb-3" />
                <h2 className="font-heading font-bold text-2xl text-[#2D3728]">
                  {authMode === 'login' ? 'Welcome back' : 'Create account'}
                </h2>
                <p className="text-[#5C6B54] text-sm font-body mt-1">
                  {authMode === 'login' ? 'Sign in to your Pantry Pulse account' : 'Start your cooking journey'}
                </p>
              </div>

              {/* Google Login */}
              <button
                data-testid="google-login-btn"
                onClick={loginWithGoogle}
                className="w-full flex items-center justify-center gap-3 bg-white border-2 border-[#E2E0D8] rounded-xl py-3 font-body font-medium text-[#2D3728] hover:bg-[#F4F1EA] hover:border-[#D5DCC9] transition-all text-sm mb-4"
              >
                <GoogleLogo size={20} weight="bold" className="text-[#CC5500]" />
                Continue with Google
              </button>

              <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 h-px bg-[#E2E0D8]" />
                <span className="text-xs text-[#5C6B54] font-body">or</span>
                <div className="flex-1 h-px bg-[#E2E0D8]" />
              </div>

              {/* Email/Password Form */}
              <form onSubmit={handleSubmit} className="space-y-3">
                {authMode === 'register' && (
                  <div className="relative">
                    <User size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#5C6B54]" />
                    <input
                      data-testid="auth-name-input"
                      type="text"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      placeholder="Full name"
                      className="w-full bg-white border border-[#E2E0D8] rounded-xl pl-10 pr-4 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                      required
                    />
                  </div>
                )}
                <div className="relative">
                  <Envelope size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#5C6B54]" />
                  <input
                    data-testid="auth-email-input"
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="Email address"
                    className="w-full bg-white border border-[#E2E0D8] rounded-xl pl-10 pr-4 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                    required
                  />
                </div>
                <div className="relative">
                  <Lock size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#5C6B54]" />
                  <input
                    data-testid="auth-password-input"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Password"
                    minLength={6}
                    className="w-full bg-white border border-[#E2E0D8] rounded-xl pl-10 pr-10 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#5C6B54] hover:text-[#2D3728]"
                  >
                    {showPassword ? <EyeSlash size={18} /> : <Eye size={18} />}
                  </button>
                </div>

                {error && (
                  <p data-testid="auth-error-message" className="text-red-600 text-sm font-body bg-red-50 rounded-lg px-3 py-2">{error}</p>
                )}

                <button
                  data-testid="auth-submit-btn"
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-[#2C5545] text-[#FDFBF7] rounded-xl py-3 font-body font-semibold hover:bg-[#3D6F5B] transition-colors text-sm disabled:opacity-60"
                >
                  {submitting ? (
                    <span className="inline-flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      {authMode === 'login' ? 'Signing in...' : 'Creating account...'}
                    </span>
                  ) : (
                    authMode === 'login' ? 'Sign In' : 'Create Account'
                  )}
                </button>
              </form>

              <p className="text-center text-sm text-[#5C6B54] font-body mt-5">
                {authMode === 'login' ? (
                  <>Don't have an account?{' '}
                    <button data-testid="switch-to-register" onClick={() => { setAuthMode('register'); setError(''); }} className="text-[#CC5500] font-medium hover:underline">Sign up</button>
                  </>
                ) : (
                  <>Already have an account?{' '}
                    <button data-testid="switch-to-login" onClick={() => { setAuthMode('login'); setError(''); }} className="text-[#CC5500] font-medium hover:underline">Sign in</button>
                  </>
                )}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
