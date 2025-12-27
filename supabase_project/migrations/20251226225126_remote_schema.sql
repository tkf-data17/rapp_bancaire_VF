drop extension if exists "pg_net";


  create table "public"."reconciliation_history" (
    "id" uuid not null default gen_random_uuid(),
    "user_id" uuid not null,
    "banque" text,
    "path" text,
    "pdf_path" text,
    "date_gen" text,
    "created_at" timestamp with time zone not null default timezone('utc'::text, now())
      );


alter table "public"."reconciliation_history" enable row level security;


  create table "public"."user_profiles" (
    "id" uuid not null,
    "email" text,
    "nom" text,
    "prenoms" text,
    "telephone" text,
    "entreprise" text,
    "credits" integer default 2,
    "created_at" timestamp with time zone not null default timezone('utc'::text, now())
      );


alter table "public"."user_profiles" enable row level security;

CREATE UNIQUE INDEX reconciliation_history_pkey ON public.reconciliation_history USING btree (id);

CREATE UNIQUE INDEX user_profiles_pkey ON public.user_profiles USING btree (id);

alter table "public"."reconciliation_history" add constraint "reconciliation_history_pkey" PRIMARY KEY using index "reconciliation_history_pkey";

alter table "public"."user_profiles" add constraint "user_profiles_pkey" PRIMARY KEY using index "user_profiles_pkey";

alter table "public"."reconciliation_history" add constraint "reconciliation_history_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) not valid;

alter table "public"."reconciliation_history" validate constraint "reconciliation_history_user_id_fkey";

alter table "public"."user_profiles" add constraint "user_profiles_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) not valid;

alter table "public"."user_profiles" validate constraint "user_profiles_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
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
$function$
;

grant delete on table "public"."reconciliation_history" to "anon";

grant insert on table "public"."reconciliation_history" to "anon";

grant references on table "public"."reconciliation_history" to "anon";

grant select on table "public"."reconciliation_history" to "anon";

grant trigger on table "public"."reconciliation_history" to "anon";

grant truncate on table "public"."reconciliation_history" to "anon";

grant update on table "public"."reconciliation_history" to "anon";

grant delete on table "public"."reconciliation_history" to "authenticated";

grant insert on table "public"."reconciliation_history" to "authenticated";

grant references on table "public"."reconciliation_history" to "authenticated";

grant select on table "public"."reconciliation_history" to "authenticated";

grant trigger on table "public"."reconciliation_history" to "authenticated";

grant truncate on table "public"."reconciliation_history" to "authenticated";

grant update on table "public"."reconciliation_history" to "authenticated";

grant delete on table "public"."reconciliation_history" to "service_role";

grant insert on table "public"."reconciliation_history" to "service_role";

grant references on table "public"."reconciliation_history" to "service_role";

grant select on table "public"."reconciliation_history" to "service_role";

grant trigger on table "public"."reconciliation_history" to "service_role";

grant truncate on table "public"."reconciliation_history" to "service_role";

grant update on table "public"."reconciliation_history" to "service_role";

grant delete on table "public"."user_profiles" to "anon";

grant insert on table "public"."user_profiles" to "anon";

grant references on table "public"."user_profiles" to "anon";

grant select on table "public"."user_profiles" to "anon";

grant trigger on table "public"."user_profiles" to "anon";

grant truncate on table "public"."user_profiles" to "anon";

grant update on table "public"."user_profiles" to "anon";

grant delete on table "public"."user_profiles" to "authenticated";

grant insert on table "public"."user_profiles" to "authenticated";

grant references on table "public"."user_profiles" to "authenticated";

grant select on table "public"."user_profiles" to "authenticated";

grant trigger on table "public"."user_profiles" to "authenticated";

grant truncate on table "public"."user_profiles" to "authenticated";

grant update on table "public"."user_profiles" to "authenticated";

grant delete on table "public"."user_profiles" to "service_role";

grant insert on table "public"."user_profiles" to "service_role";

grant references on table "public"."user_profiles" to "service_role";

grant select on table "public"."user_profiles" to "service_role";

grant trigger on table "public"."user_profiles" to "service_role";

grant truncate on table "public"."user_profiles" to "service_role";

grant update on table "public"."user_profiles" to "service_role";


  create policy "Users can insert own history"
  on "public"."reconciliation_history"
  as permissive
  for insert
  to public
with check ((auth.uid() = user_id));



  create policy "Users can view own history"
  on "public"."reconciliation_history"
  as permissive
  for select
  to public
using ((auth.uid() = user_id));



  create policy "Users can update own profile"
  on "public"."user_profiles"
  as permissive
  for update
  to public
using ((auth.uid() = id));



  create policy "Users can view own profile"
  on "public"."user_profiles"
  as permissive
  for select
  to public
using ((auth.uid() = id));


CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


  create policy "Authenticated users can upload"
  on "storage"."objects"
  as permissive
  for insert
  to public
with check (((bucket_id = 'reports'::text) AND (auth.role() = 'authenticated'::text)));



  create policy "Users can view own folder"
  on "storage"."objects"
  as permissive
  for select
  to public
using (((bucket_id = 'reports'::text) AND ((storage.foldername(name))[1] = (auth.uid())::text)));



