import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AuthCallback() {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const params = new URLSearchParams(hash.substring(1));
    const sessionId = params.get('session_id');

    if (!sessionId) {
      navigate('/');
      return;
    }

    const exchangeSession = async () => {
      try {
        const res = await axios.post(`${API}/auth/session`, { session_id: sessionId }, { withCredentials: true });
        setUser(res.data);
        navigate('/dashboard', { replace: true, state: { user: res.data } });
      } catch (e) {
        console.error('Auth exchange failed:', e);
        navigate('/');
      }
    };
    exchangeSession();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-sand-DEFAULT">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-forest-DEFAULT border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-muted-foreground font-body">Signing you in...</p>
      </div>
    </div>
  );
}
