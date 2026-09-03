  import React, { createContext, useContext, useState, useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';

const AuthContext = createContext();

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || "";
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

let supabase = null;
const isSupabaseConfigured = SUPABASE_URL && SUPABASE_KEY && !SUPABASE_URL.includes("your-project");

if (isSupabaseConfigured) {
  try {
    supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
  } catch (e) {
    console.error("Failed to initialize Supabase client on frontend:", e);
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isDemoMode, setIsDemoMode] = useState(!isSupabaseConfigured);

  useEffect(() => {
    // Check if the mock admin user is logged in
    const savedUser = localStorage.getItem('mock_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
      setLoading(false);
      return;
    }

    if (!isSupabaseConfigured) {
      setLoading(false);
      return;
    }

    // Supabase Mode
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user || null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const loginWithGoogle = async () => {
    if (isDemoMode || !supabase) {
      // Simulated OAuth login
      const mockUser = {
        id: 'mock-uuid-1234-5678',
        email: 'oxis_agent@oxis.com',
        user_metadata: {
          full_name: 'OXIS Lead Specialist',
          avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=oxis'
        }
      };
      localStorage.setItem('mock_user', JSON.stringify(mockUser));
      setUser(mockUser);
      return { user: mockUser, error: null };
    }

    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin
        }
      });
      return { data, error };
    } catch (err) {
      console.error("OAuth error:", err);
      return { data: null, error: err };
    }
  };

  const loginWithEmail = async (email, password) => {
    // Intercept default test account
    if (email === 'admin@oxis.com' && password === 'password123') {
      const mockUser = {
        id: 'mock-admin-id',
        email: email,
        user_metadata: {
          full_name: 'Admin User',
          avatar_url: `https://api.dicebear.com/7.x/bottts/svg?seed=admin`
        }
      };
      localStorage.setItem('mock_user', JSON.stringify(mockUser));
      setUser(mockUser);
      return { data: { user: mockUser }, error: null };
    }

    if (isDemoMode || !supabase) {
      // Mock email login for any other email (if in demo mode)
      const mockUser = {
        id: 'mock-uuid-1234-5678',
        email: email,
        user_metadata: {
          full_name: email.split('@')[0].toUpperCase(),
          avatar_url: `https://api.dicebear.com/7.x/initials/svg?seed=${email}`
        }
      };
      localStorage.setItem('mock_user', JSON.stringify(mockUser));
      setUser(mockUser);
      return { data: { user: mockUser }, error: null };
    }

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      return { data, error };
    } catch (err) {
      return { data: null, error: err };
    }
  };

  const logout = async () => {
    // Clear mock user if it exists
    if (localStorage.getItem('mock_user')) {
      localStorage.removeItem('mock_user');
      setUser(null);
      if (isDemoMode || !supabase) return { error: null };
    }

    if (!supabase) return { error: null };

    const { error } = await supabase.auth.signOut();
    return { error };
  };

  const value = {
    user,
    loading,
    isDemoMode,
    loginWithGoogle,
    loginWithEmail,
    logout,
    supabaseClient: supabase
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
