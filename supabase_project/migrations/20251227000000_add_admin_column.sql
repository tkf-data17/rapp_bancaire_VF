-- Ajout de la colonne is_admin pour la gestion des droits
ALTER TABLE public.user_profiles ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- (Optionnel) Commentaire pour clarification
COMMENT ON COLUMN public.user_profiles.is_admin IS 'Indique si l''utilisateur a des droits d''administrateur';
