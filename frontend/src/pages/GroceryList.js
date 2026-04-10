import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingCart, Sparkle, Plus, Trash, Tag, Storefront, CreditCard, CheckCircle, ArrowRight, Package, X, Basket } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SERVICE_FEE = 2.50;

const STORE_OPTIONS = [
  { id: 'instacart', name: 'Instacart', color: 'bg-[#43B02A]', url: 'https://www.instacart.com/store/search_v3/search?search_term=' },
  { id: 'walmart', name: 'Walmart', color: 'bg-[#0071DC]', url: 'https://www.walmart.com/search?q=' },
  { id: 'shoprite', name: 'ShopRite', color: 'bg-[#D31245]', url: 'https://www.shoprite.com/sm/pickup/rsid/3000/search?q=' },
  { id: 'amazon_fresh', name: 'Amazon Fresh', color: 'bg-[#FF9900]', url: 'https://www.amazon.com/s?k=' },
  { id: 'target', name: 'Target', color: 'bg-[#CC0000]', url: 'https://www.target.com/s?searchTerm=' },
];

export default function GroceryList() {
  const [pantryItems, setPantryItems] = useState([]);
  const [suggestions, setSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cart, setCart] = useState({ items: [], subtotal: 0, service_fee: SERVICE_FEE, total: SERVICE_FEE, item_count: 0 });
  const [selectedStore, setSelectedStore] = useState('instacart');
  const [checkingOut, setCheckingOut] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState(null);
  const [pollingStatus, setPollingStatus] = useState(false);

  const fetchCart = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/cart`, { withCredentials: true });
      setCart(res.data);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => {
    const fetchPantry = async () => {
      try {
        const res = await axios.get(`${API}/pantry`, { withCredentials: true });
        setPantryItems(res.data);
      } catch (e) { console.error(e); }
    };
    fetchPantry();
    fetchCart();
  }, [fetchCart]);

  // Check for return from Stripe
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    const status = params.get('status');
    if (sessionId && status === 'success') {
      setPollingStatus(true);
      pollPaymentStatus(sessionId, 0);
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    } else if (status === 'cancelled') {
      toast.info('Order cancelled');
      window.history.replaceState({}, '', window.location.pathname);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pollPaymentStatus = async (sessionId, attempts) => {
    if (attempts >= 8) {
      setPollingStatus(false);
      toast.error('Payment status check timed out. Please refresh.');
      return;
    }
    try {
      const res = await axios.get(`${API}/cart/checkout/status/${sessionId}`, { withCredentials: true });
      if (res.data.payment_status === 'paid') {
        setPollingStatus(false);
        setOrderSuccess({
          itemsAdded: res.data.items_added,
          storeId: res.data.store_id,
        });
        fetchCart();
        toast.success('Payment successful! Items added to your pantry.');
      } else if (res.data.status === 'expired') {
        setPollingStatus(false);
        toast.error('Payment session expired');
      } else {
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2500);
      }
    } catch (e) {
      console.error(e);
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2500);
    }
  };

  const generateSuggestions = async () => {
    setLoading(true);
    setSuggestions(null);
    try {
      const res = await axios.post(`${API}/grocery/suggestions-priced`, {
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

  const addToCart = async (item) => {
    try {
      await axios.post(`${API}/cart/add`, {
        name: item.name,
        category: item.category || 'other',
        quantity: 1,
        estimated_price: item.estimated_price || 0,
      }, { withCredentials: true });
      await fetchCart();
      toast.success(`${item.name} added to cart`);
    } catch (e) {
      toast.error('Failed to add to cart');
    }
  };

  const addAllToCart = async () => {
    if (!suggestions?.suggestions) return;
    const items = suggestions.suggestions.map(s => ({
      name: s.name,
      category: s.category || 'other',
      quantity: 1,
      estimated_price: s.estimated_price || 0,
    }));
    try {
      await axios.post(`${API}/cart/add-bulk`, { items }, { withCredentials: true });
      await fetchCart();
      toast.success(`${items.length} items added to cart`);
    } catch (e) {
      toast.error('Failed to add items');
    }
  };

  const removeFromCart = async (cartItemId) => {
    try {
      await axios.delete(`${API}/cart/${cartItemId}`, { withCredentials: true });
      await fetchCart();
    } catch (e) {
      toast.error('Failed to remove');
    }
  };

  const clearCart = async () => {
    try {
      await axios.delete(`${API}/cart`, { withCredentials: true });
      await fetchCart();
      toast.success('Cart cleared');
    } catch (e) {
      toast.error('Failed to clear cart');
    }
  };

  const checkout = async () => {
    if (cart.item_count === 0) {
      toast.error('Cart is empty');
      return;
    }
    setCheckingOut(true);
    try {
      const res = await axios.post(`${API}/cart/checkout`, {
        origin_url: window.location.origin,
        store_id: selectedStore,
      }, { withCredentials: true });
      if (res.data.url) {
        window.location.href = res.data.url;
      }
    } catch (e) {
      console.error(e);
      toast.error('Failed to start checkout');
      setCheckingOut(false);
    }
  };

  const openStoreSearch = (storeName) => {
    const store = STORE_OPTIONS.find(s => s.id === storeName);
    if (store && cart.items.length > 0) {
      const searchTerms = cart.items.length > 0 
        ? cart.items.map(i => i.name).join('+')
        : orderSuccess?.storeId ? 'groceries' : '';
      window.open(`${store.url}${encodeURIComponent(searchTerms)}`, '_blank');
    }
  };

  const isInCart = (itemName) => cart.items.some(ci => ci.name === itemName);

  const priorityColors = {
    high: 'bg-red-50 text-red-700 border-red-200',
    medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    low: 'bg-green-50 text-green-700 border-green-200',
  };

  // Polling state (returning from Stripe)
  if (pollingStatus) {
    return (
      <div className="min-h-screen bg-[#FDFBF7]">
        <Navbar />
        <div className="flex flex-col items-center justify-center py-32">
          <div className="w-16 h-16 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="font-heading font-semibold text-xl text-[#2D3728]">Processing your order...</p>
          <p className="text-[#5C6B54] font-body text-sm mt-1">Verifying payment and adding items to your pantry</p>
        </div>
      </div>
    );
  }

  // Order success state
  if (orderSuccess) {
    const store = STORE_OPTIONS.find(s => s.id === orderSuccess.storeId);
    return (
      <div className="min-h-screen bg-[#FDFBF7]">
        <Navbar />
        <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-3xl mx-auto">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-12">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle size={48} weight="fill" className="text-green-600" />
            </div>
            <h1 className="font-heading font-bold text-3xl text-[#2D3728] mb-2">Order Confirmed!</h1>
            <p className="text-[#5C6B54] font-body text-lg mb-2">{orderSuccess.itemsAdded} items have been added to your pantry</p>
            <p className="text-[#5C6B54] font-body text-sm mb-8">Now complete your grocery purchase at your chosen store</p>

            {store && (
              <button
                data-testid="go-to-store-btn"
                onClick={() => openStoreSearch(orderSuccess.storeId)}
                className={`${store.color} text-white rounded-full px-8 py-4 font-body font-semibold text-lg hover:opacity-90 transition-all inline-flex items-center gap-3 shadow-lg`}
              >
                <Storefront size={24} />
                Shop on {store.name}
                <ArrowRight size={20} />
              </button>
            )}

            <div className="mt-8 flex justify-center gap-3">
              <button
                data-testid="order-done-btn"
                onClick={() => { setOrderSuccess(null); fetchCart(); }}
                className="bg-white border border-[#E2E0D8] text-[#2D3728] rounded-full px-6 py-2.5 font-body font-medium hover:bg-[#F4F1EA] transition-colors"
              >
                Back to Grocery List
              </button>
            </div>
          </motion.div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight">
              <ShoppingCart size={28} weight="duotone" className="inline mr-2 text-[#2C5545]" />
              Smart Grocery
            </h1>
            <p className="text-[#5C6B54] font-body text-sm mt-1">Get AI suggestions, add to cart, and order from your favorite store</p>
          </motion.div>

          {/* Cart toggle button */}
          <button
            data-testid="toggle-cart-btn"
            onClick={() => setShowCart(!showCart)}
            className="relative bg-[#2C5545] text-white rounded-full px-5 py-2.5 font-body font-medium hover:bg-[#3D6F5B] transition-colors text-sm inline-flex items-center gap-2"
          >
            <Basket size={18} />
            Cart
            {cart.item_count > 0 && (
              <span className="absolute -top-2 -right-2 bg-[#CC5500] text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-bold">{cart.item_count}</span>
            )}
          </button>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left: Suggestions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Generate */}
            <button
              data-testid="generate-grocery-btn"
              onClick={generateSuggestions}
              disabled={loading}
              className="bg-[#CC5500] text-white rounded-full px-8 py-3.5 font-body font-semibold hover:bg-[#E66000] transition-colors disabled:opacity-50 inline-flex items-center gap-2"
            >
              {loading ? (
                <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Analyzing pantry...</>
              ) : (
                <><Sparkle size={20} weight="fill" /> Generate Shopping Suggestions</>
              )}
            </button>

            {loading ? (
              <div className="flex flex-col items-center py-20">
                <div className="w-16 h-16 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-[#5C6B54] font-body">Analyzing your pantry and finding the best items...</p>
              </div>
            ) : suggestions ? (
              <div className="space-y-4">
                {suggestions.meal_plan_preview && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-[#2C5545] rounded-3xl p-6 text-white">
                    <h3 className="font-heading font-semibold text-lg mb-2">What You Can Make</h3>
                    <p className="text-white/80 font-body text-sm leading-relaxed">{suggestions.meal_plan_preview}</p>
                  </motion.div>
                )}

                <div className="flex items-center justify-between">
                  <h3 className="font-heading font-semibold text-lg text-[#2D3728]">Suggested Items</h3>
                  <button
                    data-testid="add-all-to-cart-btn"
                    onClick={addAllToCart}
                    className="text-[#CC5500] text-sm font-medium hover:underline inline-flex items-center gap-1"
                  >
                    <Plus size={14} weight="bold" /> Add all to cart
                  </button>
                </div>

                <div className="space-y-3">
                  {suggestions.suggestions?.map((item, i) => {
                    const inCart = isInCart(item.name);
                    return (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.04 }}
                        className={`bg-white border rounded-2xl p-5 transition-all ${inCart ? 'border-[#2C5545] bg-[#f8fdf6]' : 'border-[#E2E0D8] hover:shadow-[0_4px_16px_rgba(44,85,69,0.06)]'}`}
                      >
                        <div className="flex items-start gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-body font-medium text-[#2D3728]">{item.name}</h4>
                              <span className={`text-xs px-2 py-0.5 rounded-full border ${priorityColors[item.priority] || priorityColors.medium}`}>
                                {item.priority}
                              </span>
                              <span className="text-sm font-semibold text-[#2C5545]">${(item.estimated_price || 0).toFixed(2)}</span>
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
                            data-testid={`add-to-cart-${i}`}
                            onClick={() => !inCart && addToCart(item)}
                            disabled={inCart}
                            className={`flex-shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-all inline-flex items-center gap-1.5 ${
                              inCart ? 'bg-[#E8ECE1] text-[#2C5545]' : 'bg-[#2C5545] text-white hover:bg-[#3D6F5B]'
                            }`}
                          >
                            {inCart ? <><CheckCircle size={16} weight="fill" /> In Cart</> : <><Plus size={16} weight="bold" /> Add</>}
                          </button>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="text-center py-20">
                <ShoppingCart size={64} weight="duotone" className="text-[#D5DCC9] mx-auto mb-4" />
                <p className="text-[#5C6B54] font-body mb-2">Your pantry has {pantryItems.length} items</p>
                <p className="text-[#5C6B54] font-body text-sm">Generate suggestions to see what to buy next</p>
              </div>
            )}
          </div>

          {/* Right: Cart + Checkout */}
          <div className={`lg:block ${showCart ? 'block' : 'hidden'}`}>
            <div className="sticky top-20">
              <div className="bg-white border border-[#E2E0D8] rounded-3xl shadow-[0_4px_20px_rgba(44,85,69,0.08)] overflow-hidden">
                <div className="bg-[#2C5545] text-white px-6 py-4 flex items-center justify-between">
                  <h3 className="font-heading font-semibold text-lg flex items-center gap-2">
                    <Basket size={20} /> Your Cart
                  </h3>
                  <span className="text-sm text-white/70">{cart.item_count} items</span>
                </div>

                <div className="p-4 max-h-[340px] overflow-y-auto scrollbar-hide">
                  {cart.items.length === 0 ? (
                    <div className="text-center py-8">
                      <Package size={36} weight="duotone" className="text-[#D5DCC9] mx-auto mb-2" />
                      <p className="text-[#5C6B54] font-body text-sm">Cart is empty</p>
                      <p className="text-[#5C6B54] font-body text-xs mt-1">Add items from suggestions</p>
                    </div>
                  ) : (
                    <AnimatePresence>
                      {cart.items.map((item) => (
                        <motion.div
                          key={item.cart_item_id}
                          layout
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -20 }}
                          className="flex items-center justify-between py-2.5 border-b border-[#F4F1EA] last:border-0"
                        >
                          <div className="min-w-0 flex-1">
                            <p className="font-body font-medium text-sm text-[#2D3728] truncate">{item.name}</p>
                            <p className="text-xs text-[#5C6B54] capitalize">{item.category}</p>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <span className="text-sm font-semibold text-[#2D3728]">${(item.estimated_price || 0).toFixed(2)}</span>
                            <button
                              data-testid={`remove-cart-${item.cart_item_id}`}
                              onClick={() => removeFromCart(item.cart_item_id)}
                              className="p-1 rounded-lg hover:bg-red-50 text-red-400 hover:text-red-500 transition-colors"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  )}
                </div>

                {cart.items.length > 0 && (
                  <>
                    {/* Totals */}
                    <div className="px-6 py-3 border-t border-[#E2E0D8] bg-[#FDFBF7] space-y-1.5">
                      <div className="flex justify-between text-sm font-body">
                        <span className="text-[#5C6B54]">Estimated Subtotal</span>
                        <span className="text-[#2D3728]">${cart.subtotal.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-sm font-body">
                        <span className="text-[#5C6B54]">Service Fee</span>
                        <span className="text-[#CC5500] font-medium">${SERVICE_FEE.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-base font-body font-semibold pt-1.5 border-t border-[#E2E0D8]">
                        <span className="text-[#2D3728]">Total</span>
                        <span className="text-[#2D3728]">${cart.total.toFixed(2)}</span>
                      </div>
                    </div>

                    {/* Store Selection */}
                    <div className="px-6 py-3 border-t border-[#E2E0D8]">
                      <p className="text-xs font-medium text-[#5C6B54] uppercase tracking-wider mb-2">Order from</p>
                      <div className="flex flex-wrap gap-2">
                        {STORE_OPTIONS.map(store => (
                          <button
                            key={store.id}
                            data-testid={`store-${store.id}`}
                            onClick={() => setSelectedStore(store.id)}
                            className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                              selectedStore === store.id
                                ? `${store.color} text-white border-transparent`
                                : 'bg-white text-[#5C6B54] border-[#E2E0D8] hover:border-[#2C5545]'
                            }`}
                          >
                            {store.name}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Checkout + Clear */}
                    <div className="px-6 py-4 border-t border-[#E2E0D8] space-y-2">
                      <button
                        data-testid="checkout-btn"
                        onClick={checkout}
                        disabled={checkingOut}
                        className="w-full bg-[#CC5500] text-white rounded-full py-3.5 font-body font-semibold hover:bg-[#E66000] transition-colors disabled:opacity-50 inline-flex items-center justify-center gap-2"
                      >
                        {checkingOut ? (
                          <><div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" /> Processing...</>
                        ) : (
                          <><CreditCard size={18} /> Checkout — ${cart.total.toFixed(2)}</>
                        )}
                      </button>
                      <button
                        data-testid="clear-cart-btn"
                        onClick={clearCart}
                        className="w-full text-red-500 text-xs font-medium hover:underline py-1 inline-flex items-center justify-center gap-1"
                      >
                        <Trash size={12} /> Clear cart
                      </button>
                      <p className="text-[10px] text-[#5C6B54] text-center font-body leading-snug">
                        ${SERVICE_FEE.toFixed(2)} service fee covers curated AI grocery list. You'll complete your grocery purchase on {STORE_OPTIONS.find(s => s.id === selectedStore)?.name || 'the store'}.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
