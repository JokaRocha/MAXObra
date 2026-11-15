revoke all on table
    public.obras,
    public.movimentos_financeiros,
    public.tarefas
from public, anon;

grant select, insert, update, delete on table
    public.obras,
    public.movimentos_financeiros,
    public.tarefas
to authenticated;

revoke all on table public.user_profiles from public, anon, authenticated;
grant select on table public.user_profiles to service_role;

revoke all on all sequences in schema public from public, anon;
grant usage, select on all sequences in schema public to authenticated;