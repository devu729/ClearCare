-- ═══════════════════════════════════════════════════════════
-- ClearCare — Complete Supabase Database Setup
-- Run this ENTIRE file in: Supabase Dashboard → SQL Editor
-- ═══════════════════════════════════════════════════════════

-- ── 1. PROFILES TABLE ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
  id         UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  role       TEXT NOT NULL CHECK (role IN ('clinician', 'patient')),
  email      TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on every new signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, role, email)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'role', 'patient'),
    NEW.email
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles;
CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- ── 2. AUDIT LOG TABLE ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  action      TEXT NOT NULL,
  resource    TEXT,
  ip_address  TEXT,
  user_agent  TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS audit_logs_user_id_idx    ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS audit_logs_created_at_idx ON public.audit_logs(created_at DESC);

-- ── 3. POLICY DOCUMENTS TABLE ─────────────────────────────────
CREATE TABLE IF NOT EXISTS public.policy_documents (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  document_id   TEXT NOT NULL UNIQUE,
  document_name TEXT NOT NULL,
  user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  total_pages   INTEGER,
  rule_chunks   INTEGER,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── 4. ROW LEVEL SECURITY ─────────────────────────────────────
ALTER TABLE public.profiles         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.policy_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own profile"
  ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own profile"
  ON public.profiles FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users view own audit logs"
  ON public.audit_logs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role inserts audit logs"
  ON public.audit_logs FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Clinicians view own documents"
  ON public.policy_documents FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service role inserts policy docs"
  ON public.policy_documents FOR INSERT WITH CHECK (auth.role() = 'service_role');

-- ═══════════════════════════════════════════════════════════
-- ✅ Done! After running:
-- Authentication → URL Configuration
--   Site URL: http://localhost:3000
--   Redirect URL: http://localhost:3000/**
-- ═══════════════════════════════════════════════════════════
