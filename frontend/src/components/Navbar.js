import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { House, CookingPot, Package, Camera, ShoppingCart, BookmarkSimple, User, List, X } from '@phosphor-icons/react';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Home', icon: House },
  { path: '/pantry', label: 'Pantry', icon: Package },
  { path: '/recipes', label: 'Recipes', icon: CookingPot },
  { path: '/scan', label: 'Scan', icon: Camera },
  { path: '/grocery', label: 'Grocery', icon: ShoppingCart },
  { path: '/saved', label: 'Saved', icon: BookmarkSimple },
];

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <nav className="sticky top-0 z-50 bg-[#FDFBF7]/80 backdrop-blur-xl border-b border-[#E2E0D8]/50">
        <div className="px-6 sm:px-12 lg:px-20 max-w-7xl mx-auto flex items-center justify-between h-16">
          <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2.5" data-testid="nav-logo">
            <img src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/bf1627652a4a5e009e74e84be99079dbe96eca13d294667f7cee5812cf142605.png" alt="Logo" className="w-8 h-8 rounded-lg" />
            <span className="font-heading font-bold text-lg text-[#2D3728] hidden sm:inline">Pantry Pulse</span>
          </button>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map(item => {
              const Icon = item.icon;
              const active = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                  onClick={() => navigate(item.path)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-body transition-colors ${
                    active ? 'bg-[#E8ECE1] text-[#2C5545] font-medium' : 'text-[#5C6B54] hover:text-[#2D3728] hover:bg-[#F4F1EA]'
                  }`}
                >
                  <Icon size={18} weight={active ? 'fill' : 'regular'} />
                  {item.label}
                </button>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <button
              data-testid="nav-profile"
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2 px-2 py-1.5 rounded-xl hover:bg-[#F4F1EA] transition-colors"
            >
              {user?.picture ? (
                <img src={user.picture} alt="" className="w-8 h-8 rounded-full object-cover" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-[#E8ECE1] flex items-center justify-center">
                  <User size={16} className="text-[#2C5545]" />
                </div>
              )}
            </button>
            <button
              data-testid="mobile-menu-btn"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-xl hover:bg-[#F4F1EA] text-[#2D3728]"
            >
              {mobileOpen ? <X size={22} /> : <List size={22} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 bg-black/20 backdrop-blur-sm" onClick={() => setMobileOpen(false)}>
          <div className="absolute top-16 left-0 right-0 bg-[#FDFBF7] border-b border-[#E2E0D8] shadow-lg p-4" onClick={e => e.stopPropagation()}>
            {NAV_ITEMS.map(item => {
              const Icon = item.icon;
              const active = location.pathname === item.path;
              return (
                <button
                  key={item.path}
                  data-testid={`mobile-nav-${item.label.toLowerCase()}`}
                  onClick={() => { navigate(item.path); setMobileOpen(false); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-body transition-colors ${
                    active ? 'bg-[#E8ECE1] text-[#2C5545] font-medium' : 'text-[#5C6B54] hover:bg-[#F4F1EA]'
                  }`}
                >
                  <Icon size={20} weight={active ? 'fill' : 'regular'} />
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
