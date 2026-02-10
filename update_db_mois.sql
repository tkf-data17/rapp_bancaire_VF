-- Ajout de la colonne 'mois' à la table d'historique
ALTER TABLE public.reconciliation_history ADD COLUMN IF NOT EXISTS mois text;

-- (Optionnel) Mise à jour des anciennes lignes avec une valeur par défaut si besoin
-- UPDATE public.reconciliation_history SET mois = 'N/A' WHERE mois IS NULL;
