create table if not exists public.user_profiles (
    user_id uuid primary key references auth.users (id) on delete cascade,
    username text not null unique
        check (username = lower(username) and username ~ '^[a-z0-9][a-z0-9._-]{2,31}$'),
    created_at timestamptz not null default now()
);

alter table public.user_profiles enable row level security;
revoke all on table public.user_profiles from public, anon, authenticated;
grant select on table public.user_profiles to authenticated;
grant select on table public.user_profiles to service_role;