-- ==============================================================================
-- SCRIPT DE CORRECTION ET MISE A JOUR DE LA BASE DE DONNEES (VERSION FINALE)
-- ==============================================================================

-- 1. Création de la table d'historique (Si elle n'existe pas encore)
CREATE TABLE IF NOT EXISTS public.reconciliation_history (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users NOT NULL,
  banque text,
  path text,
  pdf_path text,
  date_gen text,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Ajout de la colonne 'mois' (Si elle n'existe pas déjà)
ALTER TABLE public.reconciliation_history ADD COLUMN IF NOT EXISTS mois text;

-- 3. Configuration de la sécurité (Row Level Security)
ALTER TABLE public.reconciliation_history ENABLE ROW LEVEL SECURITY;

-- Suppression des anciennes politiques pour éviter les erreurs si elles existent déjà
DROP POLICY IF EXISTS "Users can view own history" ON public.reconciliation_history;
DROP POLICY IF EXISTS "Users can insert own history" ON public.reconciliation_history;

-- Recréation des politiques de sécurité
CREATE POLICY "Users can view own history" ON public.reconciliation_history
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own history" ON public.reconciliation_history
  FOR INSERT WITH CHECK (auth.uid() = user_id);


-- 4. IMPORTANT : Rechargement du cache de l'API Supabase
-- Cette commande est CRUCIALE pour que la nouvelle colonne soit visible par l'application
NOTIFY pgrst, 'reload schema';


-- Confirmation
SELECT 'Succès ! La table est à jour et le cache API a été rechargé.' as status;
