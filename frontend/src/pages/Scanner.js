import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Camera, Receipt, Barcode, UploadSimple, Plus, CheckCircle, X, VideoCamera, Stop } from '@phosphor-icons/react';
import Navbar from '../components/Navbar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Scanner() {
  const [scanning, setScanning] = useState(false);
  const [photoResult, setPhotoResult] = useState(null);
  const [receiptResult, setReceiptResult] = useState(null);
  const [barcodeResult, setBarcodeResult] = useState(null);
  const [addedItems, setAddedItems] = useState(new Set());
  const [cameraActive, setCameraActive] = useState(false);
  const [barcodeScanning, setBarcodeScanning] = useState(false);
  const scannerRef = useRef(null);
  const html5QrCodeRef = useRef(null);

  const stopBarcodeScanner = useCallback(async () => {
    if (html5QrCodeRef.current) {
      try {
        await html5QrCodeRef.current.stop();
        html5QrCodeRef.current.clear();
      } catch (e) {
        console.log('Scanner stop:', e);
      }
      html5QrCodeRef.current = null;
    }
    setCameraActive(false);
    setBarcodeScanning(false);
  }, []);

  useEffect(() => {
    return () => { stopBarcodeScanner(); };
  }, [stopBarcodeScanner]);

  const startBarcodeScanner = async () => {
    setCameraActive(true);
    setBarcodeScanning(true);
    setBarcodeResult(null);
    try {
      const { Html5Qrcode } = await import('html5-qrcode');
      await new Promise(r => setTimeout(r, 300));
      const scanner = new Html5Qrcode("barcode-reader");
      html5QrCodeRef.current = scanner;
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 280, height: 160 }, aspectRatio: 1.5 },
        async (decodedText) => {
          await scanner.stop();
          scanner.clear();
          html5QrCodeRef.current = null;
          setCameraActive(false);
          setBarcodeScanning(false);
          lookupBarcode(decodedText);
        },
        () => {}
      );
    } catch (err) {
      console.error('Camera error:', err);
      toast.error('Could not access camera. Check permissions.');
      setCameraActive(false);
      setBarcodeScanning(false);
    }
  };

  const lookupBarcode = async (code) => {
    setScanning(true);
    setBarcodeResult(null);
    try {
      const res = await axios.get(`${API}/barcode/${code}`, { withCredentials: true });
      setBarcodeResult(res.data);
      if (res.data.found) {
        toast.success(`Found: ${res.data.name}`);
      } else {
        toast.info(`Product not found for barcode: ${code}`);
      }
    } catch (e) {
      console.error(e);
      toast.error('Barcode lookup failed');
    } finally {
      setScanning(false);
    }
  };

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
          <p className="text-[#5C6B54] font-body text-sm mb-6">Scan barcodes, photograph food, or upload receipts</p>
        </motion.div>

        <Tabs defaultValue="barcode" className="w-full" onValueChange={() => stopBarcodeScanner()}>
          <TabsList className="bg-[#F4F1EA] rounded-full p-1 mb-6">
            <TabsTrigger data-testid="scan-barcode-tab" value="barcode" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-[#2D3728] text-[#5C6B54] px-5 py-2 font-body text-sm">
              <Barcode size={18} className="mr-2" /> Barcode
            </TabsTrigger>
            <TabsTrigger data-testid="scan-photo-tab" value="photo" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-[#2D3728] text-[#5C6B54] px-5 py-2 font-body text-sm">
              <Camera size={18} className="mr-2" /> Photo
            </TabsTrigger>
            <TabsTrigger data-testid="scan-receipt-tab" value="receipt" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-[#2D3728] text-[#5C6B54] px-5 py-2 font-body text-sm">
              <Receipt size={18} className="mr-2" /> Receipt
            </TabsTrigger>
          </TabsList>

          {/* BARCODE TAB */}
          <TabsContent value="barcode">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">Scan a Barcode</h3>
                <div ref={scannerRef} className="relative rounded-2xl overflow-hidden bg-black min-h-[220px] mb-4">
                  <div id="barcode-reader" className="w-full" />
                  {!cameraActive && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#F4F1EA]">
                      <Barcode size={48} weight="duotone" className="text-[#2C5545] mb-3" />
                      <p className="text-[#5C6B54] font-body text-sm">Point camera at a barcode</p>
                    </div>
                  )}
                </div>
                <div className="flex gap-3">
                  {!cameraActive ? (
                    <button
                      data-testid="start-barcode-scan-btn"
                      onClick={startBarcodeScanner}
                      className="flex-1 bg-[#2C5545] text-white rounded-full py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors inline-flex items-center justify-center gap-2"
                    >
                      <VideoCamera size={18} /> Start Camera
                    </button>
                  ) : (
                    <button
                      data-testid="stop-barcode-scan-btn"
                      onClick={stopBarcodeScanner}
                      className="flex-1 bg-red-500 text-white rounded-full py-3 font-body font-medium hover:bg-red-600 transition-colors inline-flex items-center justify-center gap-2"
                    >
                      <Stop size={18} /> Stop Camera
                    </button>
                  )}
                </div>
                {/* Manual barcode input */}
                <div className="mt-4 pt-4 border-t border-[#F4F1EA]">
                  <p className="text-xs text-[#5C6B54] mb-2 font-body">Or enter barcode manually:</p>
                  <div className="flex gap-2">
                    <input
                      data-testid="barcode-manual-input"
                      id="manual-barcode"
                      placeholder="Enter barcode number..."
                      className="flex-1 bg-white border border-[#E2E0D8] rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-[#2C5545] focus:border-transparent transition-all font-body text-sm"
                      onKeyDown={e => { if (e.key === 'Enter') { lookupBarcode(e.target.value); e.target.value = ''; } }}
                    />
                    <button
                      data-testid="barcode-lookup-btn"
                      onClick={() => { const el = document.getElementById('manual-barcode'); lookupBarcode(el.value); el.value = ''; }}
                      className="bg-[#2C5545] text-white rounded-xl px-4 py-2.5 hover:bg-[#3D6F5B] transition-colors font-body text-sm"
                    >
                      Lookup
                    </button>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-6 shadow-[0_2px_12px_rgba(44,85,69,0.04)]">
                <h3 className="font-heading font-semibold text-lg text-[#2D3728] mb-4">Product Info</h3>
                {scanning ? (
                  <div className="flex flex-col items-center py-12">
                    <div className="w-10 h-10 border-4 border-[#2C5545] border-t-transparent rounded-full animate-spin mb-3" />
                    <p className="text-[#5C6B54] font-body text-sm">Looking up product...</p>
                  </div>
                ) : barcodeResult?.found ? (
                  <div className="space-y-4">
                    <div className="flex items-start gap-4">
                      {barcodeResult.image_url && (
                        <img src={barcodeResult.image_url} alt={barcodeResult.name} className="w-20 h-20 rounded-xl object-cover flex-shrink-0" />
                      )}
                      <div>
                        <p className="font-heading font-semibold text-lg text-[#2D3728]">{barcodeResult.name}</p>
                        {barcodeResult.brand && <p className="text-sm text-[#5C6B54] font-body">{barcodeResult.brand}</p>}
                        <div className="flex flex-wrap gap-2 mt-2">
                          <span className="text-xs bg-[#E8ECE1] text-[#2C5545] px-2.5 py-1 rounded-full capitalize">{barcodeResult.category}</span>
                          {barcodeResult.quantity && <span className="text-xs text-[#5C6B54] bg-[#F4F1EA] px-2.5 py-1 rounded-full">{barcodeResult.quantity}</span>}
                          {barcodeResult.nutriscore && <span className="text-xs bg-green-50 text-green-700 px-2.5 py-1 rounded-full uppercase">Nutri: {barcodeResult.nutriscore}</span>}
                          {barcodeResult.calories && <span className="text-xs bg-orange-50 text-orange-700 px-2.5 py-1 rounded-full">{barcodeResult.calories} kcal/100g</span>}
                        </div>
                      </div>
                    </div>
                    <button
                      data-testid="add-barcode-to-pantry-btn"
                      onClick={() => addToPantry({ name: barcodeResult.name, category: barcodeResult.category, quantity: barcodeResult.quantity })}
                      disabled={addedItems.has(barcodeResult.name)}
                      className={`w-full rounded-full py-3 font-body font-medium transition-colors inline-flex items-center justify-center gap-2 ${
                        addedItems.has(barcodeResult.name)
                          ? 'bg-green-50 text-green-700'
                          : 'bg-[#CC5500] text-white hover:bg-[#E66000]'
                      }`}
                    >
                      {addedItems.has(barcodeResult.name) ? <><CheckCircle size={18} weight="fill" /> Added to Pantry</> : <><Plus size={18} weight="bold" /> Add to Pantry</>}
                    </button>
                  </div>
                ) : barcodeResult && !barcodeResult.found ? (
                  <div className="text-center py-8">
                    <Barcode size={48} weight="duotone" className="text-[#D5DCC9] mx-auto mb-3" />
                    <p className="text-[#5C6B54] font-body text-sm">Product not found for this barcode</p>
                    <p className="text-xs text-[#5C6B54] mt-1">Code: {barcodeResult.code}</p>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Barcode size={48} weight="duotone" className="text-[#D5DCC9] mx-auto mb-3" />
                    <p className="text-[#5C6B54] font-body text-sm">Scan a barcode to see product info</p>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>

          {/* PHOTO TAB */}
          <TabsContent value="photo">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-8 shadow-[0_2px_12px_rgba(44,85,69,0.04)] flex flex-col items-center justify-center min-h-[300px]">
                <img src="https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/1a8a3c53284c1ac05fa457b62feb443d373fc1f5c9129f8066e0fc9b632db36d.png" alt="Scan" className="w-28 h-28 mb-4 opacity-70" />
                <p className="text-[#5C6B54] font-body text-sm mb-4 text-center">Take a photo of your food items and our AI will identify them</p>
                <label data-testid="photo-upload-label" className="bg-[#2C5545] text-white rounded-full px-6 py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors cursor-pointer inline-flex items-center gap-2">
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
                    <button data-testid="add-all-photo-btn" onClick={() => addAllToPantry(photoResult.items)} className="mb-3 text-[#CC5500] text-sm font-medium hover:underline">+ Add all to pantry</button>
                    {photoResult.items.map((item, i) => <ItemCard key={`photo-${item.name}-${i}`} item={item} />)}
                  </>
                ) : (
                  <p className="text-[#5C6B54] font-body text-sm py-8 text-center">Upload a photo to see identified items here</p>
                )}
              </div>
            </div>
          </TabsContent>

          {/* RECEIPT TAB */}
          <TabsContent value="receipt">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white border border-[#E2E0D8] rounded-3xl p-8 shadow-[0_2px_12px_rgba(44,85,69,0.04)] flex flex-col items-center justify-center min-h-[300px]">
                <Receipt size={64} weight="duotone" className="text-[#D5DCC9] mb-4" />
                <p className="text-[#5C6B54] font-body text-sm mb-4 text-center">Snap a photo of your grocery receipt to auto-add all items</p>
                <label data-testid="receipt-upload-label" className="bg-[#2C5545] text-white rounded-full px-6 py-3 font-body font-medium hover:bg-[#3D6F5B] transition-colors cursor-pointer inline-flex items-center gap-2">
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
                    {receiptResult.store_name && <p className="text-xs text-[#5C6B54] mb-2 font-body">Store: {receiptResult.store_name}</p>}
                    <button data-testid="add-all-receipt-btn" onClick={() => addAllToPantry(receiptResult.items)} className="mb-3 text-[#CC5500] text-sm font-medium hover:underline">+ Add all to pantry</button>
                    {receiptResult.items.map((item, i) => <ItemCard key={`receipt-${item.name}-${i}`} item={item} />)}
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
