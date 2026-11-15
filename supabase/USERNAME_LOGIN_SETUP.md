# Username Login Setup

1. Apply `migrations/20261111_initial_schema.sql` and then `migrations/20261112_usernames.sql` in the Supabase SQL Editor.
2. From the project directory, log in to the Supabase CLI. It asks for an access token; enter it only in the terminal, never in the app or chat:

   ```powershell
   npx.cmd supabase login
   ```

   Then deploy directly to this project (no `supabase link` or Docker required):

   ```powershell
   npx.cmd supabase functions deploy username-login --remote=uqwdmcmcksaqplofyeeq --no-verify-jwt --use-api
   ```

   The function is intentionally callable before login. It uses the project-provided `SUPABASE_SERVICE_ROLE_KEY` server-side to resolve usernames. Never add that key to the app, Windows Credential Manager entry, or client code.
3. Configure the Supabase recovery email template to show the one-time token (`{{ .Token }}`), and make sure Auth email delivery/SMTP is configured. The app asks the user to enter that code and a new password.
4. Create each person's account in Supabase Authentication. Give the user a unique username by inserting a profile row in the SQL Editor:

   ```sql
   insert into public.user_profiles (user_id, username)
   select id, 'joao'
   from auth.users
   where email = 'the-users-auth-email';
   ```

   Usernames are 3 to 32 lowercase letters, digits, dots, underscores, or hyphens, and must start with a letter or digit.
5. Assign `role` in the user's admin-controlled `app_metadata` as `manager`, `builder`, or `info`. The app defaults missing or unknown roles to `info`.
6. Test login and password recovery in the app.

The role RLS policies in the initial migration currently scope records to each individual `user_id`. They enforce role actions, but they do not yet create shared company/workspace access between separate accounts.