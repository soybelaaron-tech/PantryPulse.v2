import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import ProtectedRoute from "./components/ProtectedRoute";
import AuthCallback from "./pages/AuthCallback";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import Pantry from "./pages/Pantry";
import RecipeGenerator from "./pages/RecipeGenerator";
import SavedRecipes from "./pages/SavedRecipes";
import Scanner from "./pages/Scanner";
import GroceryList from "./pages/GroceryList";
import MealPlanner from "./pages/MealPlanner";
import Profile from "./pages/Profile";

function AppRouter() {
  const location = useLocation();
  // Check URL fragment for session_id synchronously during render (prevents race conditions)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/pantry" element={<ProtectedRoute><Pantry /></ProtectedRoute>} />
      <Route path="/recipes" element={<ProtectedRoute><RecipeGenerator /></ProtectedRoute>} />
      <Route path="/saved" element={<ProtectedRoute><SavedRecipes /></ProtectedRoute>} />
      <Route path="/scan" element={<ProtectedRoute><Scanner /></ProtectedRoute>} />
      <Route path="/mealplan" element={<ProtectedRoute><MealPlanner /></ProtectedRoute>} />
      <Route path="/grocery" element={<ProtectedRoute><GroceryList /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
