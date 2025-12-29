-- ==============================================================================
-- SCRIPT DE CONFIGURATION SUPABASE (A exécuter dans l'éditeur SQL de Supabase)
-- ==============================================================================

-- 1. Table des profils utilisateurs
-- Cette table stockera les crédits et les informations complémentaires
create table public.user_profiles (
  id uuid references auth.users not null primary key,
  email text,
  nom text,
  prenoms text,
  telephone text,
  entreprise text,
  credits int default 2,
  is_admin boolean default false,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Active la sécurité (Row Level Security)
alter table public.user_profiles enable row level security;

-- Politique: Chacun peut voir son propre profil
create policy "Users can view own profile" on public.user_profiles
  for select using (auth.uid() = id);

-- Politique: Chacun peut modifier son propre profil (si besoin)
create policy "Users can update own profile" on public.user_profiles
  for update using (auth.uid() = id);

-- 2. Table d'historique des rapprochements
create table public.reconciliation_history (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  banque text,
  path text,
  pdf_path text,
  date_gen text, -- On stocke la date formatée pour l'affichage simple
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Active la sécurité
alter table public.reconciliation_history enable row level security;

-- Politique: Voir son historique
create policy "Users can view own history" on public.reconciliation_history
  for select using (auth.uid() = user_id);

-- Politique: Ajouter à son historique
create policy "Users can insert own history" on public.reconciliation_history
  for insert with check (auth.uid() = user_id);

-- 3. Trigger pour création automatique du profil
-- Met à jour la table user_profiles quand un utilisateur s'inscrit via Auth
create or replace function public.handle_new_user() 
returns trigger as $$
begin
  insert into public.user_profiles (id, email, credits, nom, prenoms, telephone, entreprise)
  values (
    new.id, 
    new.email, 
    2, 
    new.raw_user_meta_data->>'nom', 
    new.raw_user_meta_data->>'prenoms',
    new.raw_user_meta_data->>'telephone',
    new.raw_user_meta_data->>'entreprise'
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
