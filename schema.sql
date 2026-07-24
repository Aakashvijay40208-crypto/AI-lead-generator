-- =====================================================================
-- OXIS AI LEAD GENERATOR - SUPABASE DATABASE MIGRATION SCHEMA
-- Copy and run this script in your Supabase SQL Editor to initialize 
-- all tables, constraint keys, and schema indexes.
-- =====================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table (Holds auth user profiles mapped to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    photo_url TEXT,
    role TEXT DEFAULT 'user',
    last_login TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Row-level security for Profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow users to read profiles" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Allow users to update own profiles" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- 2. Search History Log Table
CREATE TABLE IF NOT EXISTS public.search_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    user_id UUID, -- Optional foreign key if mapped to auth.users
    query JSONB NOT NULL, -- Holds { city, area, radius, category, limit }
    status TEXT DEFAULT 'running', -- 'running' | 'completed' | 'failed'
    leads_found INTEGER DEFAULT 0
);

-- 3. Business Listings Table (Locations metadata from SerpAPI)
CREATE TABLE IF NOT EXISTS public.businesses (
    place_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    address TEXT,
    phone_number TEXT,
    website TEXT,
    google_rating NUMERIC(3, 2),
    review_count INTEGER,
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    last_audited_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_businesses_website ON public.businesses(website);
CREATE INDEX IF NOT EXISTS idx_businesses_category ON public.businesses(category);

-- 4. Website Technical Audits Table (SEO, UX, SSL checks)
CREATE TABLE IF NOT EXISTS public.audit_reports (
    place_id TEXT REFERENCES public.businesses(place_id) ON DELETE CASCADE PRIMARY KEY,
    website_status INTEGER,
    is_https BOOLEAN DEFAULT false,
    response_time_ms INTEGER,
    seo JSONB,            -- { title, description, h1Hierarchy, canonical, hasRobots, hasSitemap }
    ux JSONB,             -- { isMobileFriendly, hasHeroSection, hasCTA, hasFooter }
    tech_detected JSONB,  -- { bookingSystem, whatsapp, chatWidget, crm, paymentGateway, newsletter, facebookPixel, googleAnalytics }
    contacts JSONB,       -- { emails: [], phoneNumbers: [], socialLinks: { linkedin, facebook, instagram, twitter, youtube } }
    screenshots JSONB     -- { desktopUrl, mobileUrl }
);

-- 5. Lead Scores and AI Consultancy Pitches Table
CREATE TABLE IF NOT EXISTS public.lead_scores (
    place_id TEXT REFERENCES public.businesses(place_id) ON DELETE CASCADE PRIMARY KEY,
    score INTEGER NOT NULL,
    priority TEXT NOT NULL, -- 'HOT' | 'MEDIUM' | 'LOW'
    failed_checks TEXT[] DEFAULT '{}',
    recommended_services TEXT[] DEFAULT '{}',
    personalized_pitch TEXT,
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_lead_scores_priority ON public.lead_scores(priority);
CREATE INDEX IF NOT EXISTS idx_lead_scores_score ON public.lead_scores(score);

-- Enable RLS for all business data
ALTER TABLE public.businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lead_scores ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users full read/write access (internal platform for 3-4 users)
CREATE POLICY "Allow authenticated reads on businesses" ON public.businesses FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated writes on businesses" ON public.businesses FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated reads on search_history" ON public.search_history FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated writes on search_history" ON public.search_history FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated reads on audits" ON public.audit_reports FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated writes on audits" ON public.audit_reports FOR ALL TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated reads on scores" ON public.lead_scores FOR SELECT TO authenticated USING (true);
CREATE POLICY "Allow authenticated writes on scores" ON public.lead_scores FOR ALL TO authenticated USING (true) WITH CHECK (true);
