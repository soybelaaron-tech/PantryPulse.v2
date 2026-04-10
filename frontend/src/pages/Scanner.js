import React, { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Camera, Receipt, UploadSimple, Plus, CheckCircle, X } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Scanner() {
  const [scanning, setScanning] = useState(false);
  const [photoResult, setPhotoResult] = useState(null);
  const [receiptResult, setReceiptResult] = useState(null);
  const [addedItems, setAddedItems] = useState(new Set());

  const handlePhotoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setScanning(true);
    setPhotoResult(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API}/scan/photo`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setPhotoResult(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to scan photo. Try again!');
    } finally {
      setScanning(false);
    }
  };

  const handleReceiptUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setScanning(true);
    setReceiptResult(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API}/scan/receipt`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setReceiptResult(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Failed to scan receipt. Try again!');
    } finally {
      setScanning(false);
    }
  };

  const addToPantry = async (item) => {
    try {
      await axios.post(`${API}/pantry`, {
        name: item.name,
        category: item.category || 'other',
        quantity: item.quantity || null,
      }, { withCredentials: true });
      setAddedItems(new Set([...addedItems, item.name]));
      toast.success(`${item.name} added to pantry`);
    } catch (e) {
      toast.error('Failed to add item');
    }
  };

  const addAllToPantry = async (items) => {
    const toAdd = items.filter(i => !addedItems.has(i.name));
    try {
      await axios.post(`${API}/pantry/bulk`, {
        items: toAdd.map(i => ({ name: i.name, category: i.category || 'other', quantity: i.quantity || null }))
      }, { withCredentials: true });
      setAddedItems(new Set([...addedItems, ...toAdd.map(i => i.name)]));
      toast.success(`${toAdd.length} items added to pantry`);
    } catch (e) {
      toast.error('Failed to add items');
    }
  };

  const ItemCard = ({ item }) => {
    const isAdded = addedItems.has(item.name);
    return (
      <div className="flex items-center justify-between py-3 border-b border-[#F4F1EA] last:border-0">
        <div>
          <p className="font-body font-medium text-[#2D3728] text-sm">{item.name}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs bg-[#E8ECE1] text-[#2C5545] px-2 py-0.5 rounded-full capitalize">{item.category}</span>
            {item.quantity && <span className="text-xs text-[#5C6B54]">{item.quantity}</span>}
            {item.price && <span className="text-xs text-[#5C6B54]">${item.price}</span>}
          </div>
        </div>
        <button
          data-testid={`add-scanned-${item.name.toLowerCase().replace(/\s/g, '-')}`}
          onClick={() => addToPantry(item)}
          disabled={isAdded}
          className={`p-2 rounded-xl transition-colors ${isAdded ? 'text-green-600 bg-green-50' : 'text-[#2C5545] hover:bg-[#E8ECE1]'}`}
        >
          {isAdded ? <CheckCircle size={20} weight="fill" /> : <Plus size={20} weight="bold" />}
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7]">
      <Navbar />
      <main className="px-6 sm:px-12 lg:px-20 py-8 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="font-heading font-bold text-3xl text-[#2D3728] tracking-tight mb-1">Scan & Add</h1>
          <p className="text-[#5C6B54] font-body text-sm mb-6">Take a photo of food items or scan a grocery receipt</p>
        </motion.div>

        <Tabs defaultValue="photo" className="w-full">
          <TabsList className="bg-[#F4F1EA] rounded-full p-1 mb-6">
            <TabsTrigger data-testid="scan-photo-tab" value="photo" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-[#2D3728] text-[#5C6B54] px-6 py-2 font-body text-sm">
              <Camera size={18} className="mr-2" /> Photo
            </TabsTrigger>
            <TabsTrigger data-testid="scan-receipt-tab" value="receipt" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-[#2D3728] text-[#5C6B54] px-6 py-2 font-body text-sm">
              <Receipt size={18} className="mr-2" /> Receipt
            </TabsTrigger>
          </TabsList>

          <TabsContent value="photo">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-8 shadow-[0_2px_12px_rgba(44,85,69,0.04)] flex flex-col items-center justify-center min-h-[300px]">
                <img
                  src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/1a8a3c53284c1ac05fa457b62feb443d373fc1f5c9129f8066e0fc9b632db36d.png"
                  alt="Scan"
                  className="w-28 h-28 mb-4 opacity-70"
                />
                <p className="text-[#5C6B54] font-body text-sm mb-4 text-center">Take a photo of your food items and our AI will identify them</p>
                <label
                  data-testid="photo-upload-label"
                  className="bg-[#2C5545] text-white rounded-full px-6 py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors cursor-pointer inline-flex items-center gap-2"
                >
                  <UploadSimple size={18} /> Upload Photo
                  <input type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
                </label>
              </div>
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">Identified Items</h3>
                {scanning ? (
                  <div className="flex flex-col items-center py-12">
                    <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-3" />
                    <p className="text-[#5C6B54] font-body text-sm">AI is analyzing your photo...</p>
                  </div>
                ) : photoResult?.items?.length > 0 ? (
                  <>
                    <button
                      data-testid="add-all-photo-btn"
                      onClick={() => addAllToPantry(photoResult.items)}
                      className="mb-3 text-[#CC5500] text-sm font-medium hover:underline"
                    >
                      + Add all to pantry
                    </button>
                    {photoResult.items.map((item, i) => <ItemCard key={i} item={item} />)}
                  </>
                ) : (
                  <p className="text-[#5C6B54] font-body text-sm py-8 text-center">Upload a photo to see identified items here</p>
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="receipt">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-8 shadow-[0_2px_12px_rgba(44,85,69,0.04)] flex flex-col items-center justify-center min-h-[300px]">
                <Receipt size={64} weight="duotone" className="text-[#D5DCC9] mb-4" />
                <p className="text-[#5C6B54] font-body text-sm mb-4 text-center">Snap a photo of your grocery receipt to auto-add all items</p>
                <label
                  data-testid="receipt-upload-label"
                  className="bg-[#2C5545] text-white rounded-full px-6 py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors cursor-pointer inline-flex items-center gap-2"
                >
                  <UploadSimple size={18} /> Upload Receipt
                  <input type="file" accept="image/*" onChange={handleReceiptUpload} className="hidden" />
                </label>
              </div>
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">Receipt Items</h3>
                {scanning ? (
                  <div className="flex flex-col items-center py-12">
                    <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-3" />
                    <p className="text-[#5C6B54] font-body text-sm">Reading your receipt...</p>
                  </div>
                ) : receiptResult?.items?.length > 0 ? (
                  <>
                    {receiptResult.store_name && (
                      <p className="text-xs text-[#5C6B54] mb-2 font-body">Store: {receiptResult.store_name}</p>
                    )}
                    <button
                      data-testid="add-all-receipt-btn"
                      onClick={() => addAllToPantry(receiptResult.items)}
                      className="mb-3 text-[#CC5500] text-sm font-medium hover:underline"
                    >
                      + Add all to pantry
                    </button>
                    {receiptResult.items.map((item, i) => <ItemCard key={i} item={item} />)}
                    {receiptResult.total && (
                      <div className="mt-3 pt-3 border-t border-[#E2E0D8] flex justify-between text-sm font-body">
                        <span className="text-[#5C6B54]">Total</span>
                        <span className="font-semibold text-[#2D3728]">${receiptResult.total}</span>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-[#5C6B54] font-body text-sm py-8 text-center">Upload a receipt to see items here</p>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
