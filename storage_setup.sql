-- ==============================================================================
-- MISE A JOUR STOCKAGE (A exécuter dans l'éditeur SQL de Supabase)
-- ==============================================================================

-- 1. Création du bucket 'reports' s'il n'existe pas déjà
-- Note: Le dashboard Supabase est souvent mieux pour créer les buckets,
-- mais voici la commande si votre projet supporte l'API admin storage via SQL.
insert into storage.buckets (id, name, public)
values ('reports', 'reports', true)
on conflict (id) do nothing;

-- 2. Politiques de sécurité pour le stockage (Storage RLS)

-- Permettre aux utilisateurs authentifiés d'uploader dans leur propre dossier
-- (On organise par user_id/filename pour la sécurité)
create policy "Users can upload own reports"
on storage.objects for insert
with check (
  bucket_id = 'reports' AND
  auth.uid() = owner
);

-- Permettre aux utilisateurs de lire leurs propres fichiers
create policy "Users can view own reports"
on storage.objects for select
using (
  bucket_id = 'reports' AND
  auth.uid() = owner
);

-- Permettre aux utilisateurs de supprimer leurs propres fichiers (optionnel)
create policy "Users can delete own reports"
on storage.objects for delete
using (
  bucket_id = 'reports' AND
  auth.uid() = owner
);
