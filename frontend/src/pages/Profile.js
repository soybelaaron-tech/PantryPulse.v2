import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { User, Leaf, FloppyDisk, SignOut } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Slider } from '../components/ui/slider';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ALLERGY_OPTIONS = ['Peanuts', 'Tree Nuts', 'Milk', 'Eggs', 'Wheat', 'Soy', 'Fish', 'Shellfish', 'Sesame'];
const DIETARY_OPTIONS = ['Vegetarian', 'Vegan', 'Gluten-Free', 'Dairy-Free', 'Keto', 'Paleo', 'Low-Carb', 'Halal', 'Kosher'];

export default function Profile() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchProfile = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/profile`, { withCredentials: true });
      setProfile(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  const toggleAllergy = (a) => {
    const allergies = profile.allergies || [];
    setProfile({
      ...profile,
      allergies: allergies.includes(a) ? allergies.filter(x => x !== a) : [...allergies, a]
    });
  };

  const toggleDietary = (d) => {
    const prefs = profile.dietary_preferences || [];
    setProfile({
      ...profile,
      dietary_preferences: prefs.includes(d) ? prefs.filter(x => x !== d) : [...prefs, d]
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/profile`, {
        allergies: profile.allergies,
        dietary_preferences: profile.dietary_preferences,
        skill_level: profile.skill_level,
        default_servings: profile.default_servings,
        calorie_target: profile.calorie_target,
      }, { withCredentials: true });
      toast.success('Profile saved!');
    } catch (e) {
      toast.error('Failed to save profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FDFBF7]">
        <Navbar />
        <div className="flex items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-3xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {/* User Info */}
          <div className="flex items-center gap-4 mb-8">
            {user?.picture ? (
              <img src={user.picture} alt={user.name} className="w-16 h-16 rounded-2xl object-cover" />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-[#E8ECE1] flex items-center justify-center">
                <User size={28} className="text-[#2C5545]" />
              </div>
            )}
            <div>
              <h1 className="font-heading font-bold text-2xl text-[#2D3728]">{user?.name || 'User'}</h1>
              <p className="text-[#5C6B54] font-body text-sm">{user?.email}</p>
            </div>
          </div>

          {/* Settings Cards */}
          <div className="space-y-6">
            {/* Allergies */}
            <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
              <h2 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">
                <Leaf size={20} weight="duotone" className="inline mr-2 text-[#CC5500]" />
                Allergies
              </h2>
              <p className="text-[#5C6B54] font-body text-sm mb-3">Select any food allergies. AI will avoid these in recipes.</p>
              <div className="flex flex-wrap gap-2">
                {ALLERGY_OPTIONS.map(a => (
                  <button
                    key={a}
                    data-testid={`allergy-${a.toLowerCase()}`}
                    onClick={() => toggleAllergy(a)}
                    className={`text-sm px-4 py-2 rounded-full border transition-colors ${
                      profile?.allergies?.includes(a) ? 'bg-red-500 text-white border-red-500' : 'bg-white text-[#5C6B54] border-[#E2E0D8] hover:border-red-300'
                    }`}
                  >
                    {a}
                  </button>
                ))}
              </div>
            </div>

            {/* Dietary Preferences */}
            <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
              <h2 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">Dietary Preferences</h2>
              <div className="flex flex-wrap gap-2">
                {DIETARY_OPTIONS.map(d => (
                  <button
                    key={d}
                    data-testid={`dietary-pref-${d.toLowerCase()}`}
                    onClick={() => toggleDietary(d)}
                    className={`text-sm px-4 py-2 rounded-full border transition-colors ${
                      profile?.dietary_preferences?.includes(d) ? 'bg-[#2C5545] text-white border-[#2C5545]' : 'bg-white text-[#5C6B54] border-[#E2E0D8] hover:border-[#2C5545]'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {/* Cooking Settings */}
            <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
              <h2 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">Cooking Settings</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Skill Level</label>
                  <Select value={profile?.skill_level || 'beginner'} onValueChange={v => setProfile({ ...profile, skill_level: v })}>
                    <SelectTrigger data-testid="profile-skill-select" className="rounded-xl border-[#E2E0D8]"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">Default Servings: {profile?.default_servings || 2}</label>
                  <Slider
                    data-testid="profile-servings-slider"
                    value={[profile?.default_servings || 2]}
                    onValueChange={([v]) => setProfile({ ...profile, default_servings: v })}
                    min={1} max={12} step={1}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2 block">
                    Daily Calorie Target: {profile?.calorie_target || 'Not set'}
                  </label>
                  <Slider
                    data-testid="profile-calorie-slider"
                    value={[profile?.calorie_target || 0]}
                    onValueChange={([v]) => setProfile({ ...profile, calorie_target: v || null })}
                    max={4000} step={100}
                  />
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-3">
              <button
                data-testid="save-profile-btn"
                onClick={handleSave}
                disabled={saving}
                className="flex-1 bg-[#2C5545] text-[#FDFBF7] rounded-full py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors inline-flex items-center justify-center gap-2"
              >
                <FloppyDisk size={18} />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                data-testid="logout-btn"
                onClick={logout}
                className="bg-white border border-[#E2E0D8] text-red-500 rounded-full px-6 py-3 font-body font-medium hover:bg-red-50 transition-colors inline-flex items-center gap-2"
              >
                <SignOut size={18} /> Logout
              </button>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
