import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash, PencilSimple, FunnelSimple, MagnifyingGlass, X } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Calendar } from '../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { format } from 'date-fns';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORIES = [
  { value: 'protein', label: 'Protein', color: 'bg-red-50 text-red-700 border-red-200' },
  { value: 'dairy', label: 'Dairy', color: 'bg-blue-50 text-blue-700 border-blue-200' },
  { value: 'vegetable', label: 'Vegetables', color: 'bg-green-50 text-green-700 border-green-200' },
  { value: 'fruit', label: 'Fruits', color: 'bg-purple-50 text-purple-700 border-purple-200' },
  { value: 'grain', label: 'Grains', color: 'bg-amber-50 text-amber-700 border-amber-200' },
  { value: 'spice', label: 'Spices', color: 'bg-orange-50 text-orange-700 border-orange-200' },
  { value: 'condiment', label: 'Condiments', color: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
  { value: 'beverage', label: 'Beverages', color: 'bg-teal-50 text-teal-700 border-teal-200' },
  { value: 'snack', label: 'Snacks', color: 'bg-pink-50 text-pink-700 border-pink-200' },
  { value: 'other', label: 'Other', color: 'bg-gray-50 text-gray-700 border-gray-200' },
];

function getCategoryStyle(cat) {
  return CATEGORIES.find(c => c.value === cat)?.color || 'bg-gray-50 text-gray-700 border-gray-200';
}

export default function Pantry() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('all');
  const [showAdd, setShowAdd] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [form, setForm] = useState({ name: '', category: 'other', quantity: '', unit: '', expiry_date: '', notes: '' });
  const [expiryDate, setExpiryDate] = useState(null);

  const fetchItems = async () => {
    try {
      const res = await axios.get(`${API}/pantry`, { withCredentials: true });
      setItems(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchItems(); }, []);

  const handleAdd = async () => {
    if (!form.name.trim()) return;
    const payload = { ...form, expiry_date: expiryDate ? expiryDate.toISOString() : null };
    try {
      if (editItem) {
        await axios.put(`${API}/pantry/${editItem.item_id}`, payload, { withCredentials: true });
      } else {
        await axios.post(`${API}/pantry`, payload, { withCredentials: true });
      }
      await fetchItems();
      resetForm();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (itemId) => {
    try {
      await axios.delete(`${API}/pantry/${itemId}`, { withCredentials: true });
      setItems(items.filter(i => i.item_id !== itemId));
    } catch (e) {
      console.error(e);
    }
  };

  const startEdit = (item) => {
    setEditItem(item);
    setForm({ name: item.name, category: item.category, quantity: item.quantity || '', unit: item.unit || '', expiry_date: item.expiry_date || '', notes: item.notes || '' });
    setExpiryDate(item.expiry_date ? new Date(item.expiry_date) : null);
    setShowAdd(true);
  };

  const resetForm = () => {
    setForm({ name: '', category: 'other', quantity: '', unit: '', expiry_date: '', notes: '' });
    setExpiryDate(null);
    setEditItem(null);
    setShowAdd(false);
  };

  const filtered = items.filter(item => {
    const matchSearch = item.name.toLowerCase().includes(search.toLowerCase());
    const matchCat = filterCat === 'all' || item.category === filterCat;
    return matchSearch && matchCat;
  });

  const grouped = {};
  filtered.forEach(item => {
    const cat = item.category || 'other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  });

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight">My Pantry</h1>
            <p className="text-[#5C6B54] text-sm font-body mt-1">{items.length} items tracked</p>
          </div>
          <Dialog open={showAdd} onOpenChange={(open) => { if (!open) resetForm(); setShowAdd(open); }}>
            <DialogTrigger asChild>
              <button data-testid="add-pantry-item-btn" className="bg-[#2C5545] text-[#FDFBF7] rounded-full px-5 py-2.5 font-body font-medium hover:bg-[#3D6F5B] transition-colors text-sm inline-flex items-center gap-2">
                <Plus size={18} weight="bold" /> Add Item
              </button>
            </DialogTrigger>
            <DialogContent className="bg-white rounded-3xl border-[#E2E0D8] max-w-md">
              <DialogHeader>
                <DialogTitle className="font-heading font-semibold text-xl text-[#2D3728]">
                  {editItem ? 'Edit Item' : 'Add to Pantry'}
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-2">
                <input
                  data-testid="pantry-item-name-input"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="Item name (e.g. Chicken Breast)"
                  className="w-full bg-white border border-[#E2E0D8] rounded-xl px-4 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                />
                <Select value={form.category} onValueChange={v => setForm({ ...form, category: v })}>
                  <SelectTrigger data-testid="pantry-category-select" className="rounded-xl border-[#E2E0D8]">
                    <SelectValue placeholder="Category" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map(c => (
                      <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="grid grid-cols-2 gap-3">
                  <input
                    data-testid="pantry-quantity-input"
                    value={form.quantity}
                    onChange={e => setForm({ ...form, quantity: e.target.value })}
                    placeholder="Quantity"
                    className="bg-white border border-[#E2E0D8] rounded-xl px-4 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                  />
                  <input
                    data-testid="pantry-unit-input"
                    value={form.unit}
                    onChange={e => setForm({ ...form, unit: e.target.value })}
                    placeholder="Unit (lbs, oz, cups)"
                    className="bg-white border border-[#E2E0D8] rounded-xl px-4 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                  />
                </div>
                <Popover>
                  <PopoverTrigger asChild>
                    <button data-testid="pantry-expiry-date-btn" className="w-full text-left bg-white border border-[#E2E0D8] rounded-xl px-4 py-3 font-body text-sm text-[#5C6B54]">
                      {expiryDate ? format(expiryDate, 'PPP') : 'Expiry Date (optional)'}
                    </button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar mode="single" selected={expiryDate} onSelect={setExpiryDate} initialFocus />
                  </PopoverContent>
                </Popover>
                <input
                  data-testid="pantry-notes-input"
                  value={form.notes}
                  onChange={e => setForm({ ...form, notes: e.target.value })}
                  placeholder="Notes (optional)"
                  className="w-full bg-white border border-[#E2E0D8] rounded-xl px-4 py-3 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                />
                <button
                  data-testid="pantry-save-btn"
                  onClick={handleAdd}
                  className="w-full bg-[#2C5545] text-[#FDFBF7] rounded-full py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors"
                >
                  {editItem ? 'Update Item' : 'Add to Pantry'}
                </button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Search & Filter */}
        <div className="flex flex-wrap gap-3 mb-6">
          <div className="relative flex-1 min-w-[200px]">
            <MagnifyingGlass size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#5C6B54]" />
            <input
              data-testid="pantry-search-input"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search ingredients..."
              className="w-full bg-white border border-[#E2E0D8] rounded-xl pl-10 pr-4 py-2.5 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
            />
          </div>
          <Select value={filterCat} onValueChange={setFilterCat}>
            <SelectTrigger data-testid="pantry-filter-select" className="w-[160px] rounded-xl border-[#E2E0D8]">
              <FunnelSimple size={16} className="mr-1" />
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {CATEGORIES.map(c => (
                <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Items Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <img src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/f4e62cb7650b50067854b3bd5d01361e8015e4a5d18df085abc4ab7ae4546321.png" alt="Empty" className="w-40 mx-auto mb-4 opacity-60" />
            <p className="text-[#5C6B54] font-body">No items found. Add some ingredients to get started!</p>
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(grouped).map(([cat, catItems]) => (
              <motion.div key={cat} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] capitalize mb-3">
                  {CATEGORIES.find(c => c.value === cat)?.label || cat}
                  <span className="text-[#5C6B54] text-sm font-normal ml-2">({catItems.length})</span>
                </h3>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  <AnimatePresence>
                    {catItems.map(item => {
                      let expiryLabel = null;
                      if (item.expiry_date) {
                        const d = new Date(item.expiry_date);
                        const diff = Math.ceil((d - new Date()) / (1000 * 60 * 60 * 24));
                        if (diff <= 0) expiryLabel = { text: 'Expired', cls: 'bg-red-100 text-red-700' };
                        else if (diff <= 3) expiryLabel = { text: `${diff}d left`, cls: 'bg-orange-100 text-orange-700' };
                        else expiryLabel = { text: format(d, 'MMM d'), cls: 'bg-[#E8ECE1] text-[#2C5545]' };
                      }
                      return (
                        <motion.div
                          key={item.item_id}
                          layout
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="bg-white border border-[#E2E0D8] rounded-2xl p-4 hover:shadow-[0_4px_16px_rgba(44,85,69,0.06)] transition-all group"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-body font-medium text-[#2D3728]">{item.name}</p>
                              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                                <span className={`text-xs px-2 py-0.5 rounded-full border ${getCategoryStyle(item.category)}`}>
                                  {CATEGORIES.find(c => c.value === item.category)?.label || item.category}
                                </span>
                                {item.quantity && (
                                  <span className="text-xs text-[#5C6B54]">{item.quantity}{item.unit ? ` ${item.unit}` : ''}</span>
                                )}
                                {expiryLabel && (
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${expiryLabel.cls}`}>{expiryLabel.text}</span>
                                )}
                              </div>
                              {item.notes && <p className="text-xs text-[#5C6B54] mt-1.5">{item.notes}</p>}
                            </div>
                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button data-testid={`edit-item-${item.item_id}`} onClick={() => startEdit(item)} className="p-1.5 rounded-lg hover:bg-[#F4F1EA] text-[#5C6B54]">
                                <PencilSimple size={16} />
                              </button>
                              <button data-testid={`delete-item-${item.item_id}`} onClick={() => handleDelete(item.item_id)} className="p-1.5 rounded-lg hover:bg-red-50 text-red-500">
                                <Trash size={16} />
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
