-- ==============================================================================
-- SUPPRESSION DE L'HISTORIQUE PDF POUR L'UTILISATEUR 'projetdata17@gmail.com'
-- ==============================================================================

-- Option 1 : Suppression directe via une sous-requête (Le plus rapide)
DELETE FROM public.reconciliation_history
WHERE user_id = (
    SELECT id 
    FROM auth.users 
    WHERE email = 'projetdata17@gmail.com'
);

-- Option 2 : Si vous préférez vérifier l'ID d'abord
-- Étape A : Récupérer l'ID
-- SELECT id FROM auth.users WHERE email = 'projetdata17@gmail.com';

-- Étape B : Utiliser l'ID trouvé (remplacer UUID_TROUVE)
-- DELETE FROM public.reconciliation_history WHERE user_id = 'UUID_TROUVE';
