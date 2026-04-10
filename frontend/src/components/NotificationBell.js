import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bell, Warning, X, ArrowRight } from '@phosphor-icons/react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [hasNew, setHasNew] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await axios.get(`${API}/notifications/expiring`, { withCredentials: true });
        const items = res.data.notifications || [];
        setNotifications(items);
        if (items.length > 0) {
          setHasNew(true);
          // Browser push notification for critical items
          if ('Notification' in window && Notification.permission === 'granted') {
            const critical = items.filter(n => n.urgency === 'expired' || n.urgency === 'today' || n.urgency === 'critical');
            if (critical.length > 0) {
              new Notification('Pantry Pulse', {
                body: `${critical.length} item${critical.length > 1 ? 's' : ''} expiring soon!`,
                icon: 'https://static.prod-images.emergentagent.com/jobs/92889a24-3cf9-4b50-8107-eb1a43bf7294/images/bf1627652a4a5e009e74e84be99079dbe96eca13d294667f7cee5812cf142605.png'
              });
            }
          }
        }
      } catch (e) {
        console.error('Notification fetch error:', e);
      }
    };
    fetchNotifications();
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
    // Poll every 5 minutes
    const interval = setInterval(fetchNotifications, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const urgencyStyles = {
    expired: 'bg-red-100 text-red-700 border-red-200',
    today: 'bg-red-50 text-red-600 border-red-200',
    critical: 'bg-orange-50 text-orange-700 border-orange-200',
    warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        data-testid="notification-bell-btn"
        onClick={() => { setOpen(!open); setHasNew(false); }}
        className="relative p-2 rounded-xl hover:bg-[#F4F1EA] transition-colors text-[#2D3728]"
      >
        <Bell size={20} weight={open ? 'fill' : 'regular'} />
        {hasNew && notifications.length > 0 && (
          <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-[#CC5500] rounded-full border-2 border-[#FDFBF7]" />
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-[#E2E0D8] rounded-2xl shadow-[0_12px_40px_rgba(44,85,69,0.12)] overflow-hidden z-50">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#F4F1EA]">
            <h3 className="font-heading font-semibold text-sm text-[#2D3728]">
              <Warning size={16} weight="duotone" className="inline mr-1 text-[#CC5500]" />
              Expiring Items ({notifications.length})
            </h3>
            <button onClick={() => setOpen(false)} className="text-[#5C6B54] hover:text-[#2D3728]">
              <X size={16} />
            </button>
          </div>
          <div className="max-h-72 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="px-4 py-6 text-center">
                <p className="text-[#5C6B54] font-body text-sm">No items expiring soon!</p>
              </div>
            ) : (
              notifications.slice(0, 10).map((n, i) => (
                <div key={n.item_id || i} className="px-4 py-3 border-b border-[#F4F1EA] last:border-0 hover:bg-[#FDFBF7] transition-colors">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-body font-medium text-sm text-[#2D3728]">{n.name}</p>
                      <span className={`inline-block text-xs px-2 py-0.5 rounded-full border mt-1 ${urgencyStyles[n.urgency] || urgencyStyles.warning}`}>
                        {n.message}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          {notifications.length > 0 && (
            <button
              data-testid="view-all-expiring-btn"
              onClick={() => { navigate('/pantry'); setOpen(false); }}
              className="w-full px-4 py-3 text-center text-sm font-medium text-[#2C5545] hover:bg-[#F4F1EA] transition-colors border-t border-[#F4F1EA] flex items-center justify-center gap-1"
            >
              View Pantry <ArrowRight size={14} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
