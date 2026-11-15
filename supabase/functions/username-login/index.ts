import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

Deno.serve(async (request: Request) => {
  if (request.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (request.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  let input: {
    action?: unknown;
    username?: unknown;
    password?: unknown;
    token?: unknown;
  };
  try {
    input = await request.json();
  } catch {
    return jsonResponse({ error: "Invalid request" }, 400);
  }

  const username = typeof input.username === "string" ? input.username.trim().toLowerCase() : "";
  const action = input.action === "request_recovery" || input.action === "complete_recovery"
    ? input.action
    : "login";
  const password = typeof input.password === "string" ? input.password : "";
  const token = typeof input.token === "string" ? input.token.trim() : "";
  if (!/^[a-z0-9][a-z0-9._-]{2,31}$/.test(username)) {
    return jsonResponse({ error: "Invalid request" }, 400);
  }
  if (action === "login" && (password.length < 1 || password.length > 256)) {
    return jsonResponse({ error: "Invalid username or password" }, 401);
  }
  if (action === "complete_recovery" && (token.length < 6 || password.length < 8 || password.length > 256)) {
    return jsonResponse({ error: "Invalid recovery details" }, 400);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const publishableKey = request.headers.get("apikey");
  if (!supabaseUrl || !serviceRoleKey || !publishableKey) {
    return jsonResponse({ error: "Authentication service is not configured" }, 500);
  }

  try {
    const adminClient = createClient(supabaseUrl, serviceRoleKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: profile, error: profileError } = await adminClient
      .from("user_profiles")
      .select("user_id")
      .eq("username", username)
      .maybeSingle();

    if (profileError || !profile) {
      if (action === "request_recovery") {
        return jsonResponse({ message: "If the username exists, a recovery code has been sent." });
      }
      return jsonResponse({ error: "Invalid username or password" }, 401);
    }

    const { data: userResult, error: userError } = await adminClient.auth.admin.getUserById(profile.user_id);
    const email = userResult.user?.email;
    if (userError || !email) {
      if (action === "request_recovery") {
        return jsonResponse({ message: "If the username exists, a recovery code has been sent." });
      }
      return jsonResponse({ error: "Invalid username or password" }, 401);
    }

    if (action === "request_recovery") {
      const recoveryResponse = await fetch(`${supabaseUrl}/auth/v1/recover`, {
        method: "POST",
        headers: {
          "apikey": publishableKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });
      if (!recoveryResponse.ok) {
        console.error("Supabase recovery email request failed");
      }
      return jsonResponse({ message: "If the username exists, a recovery code has been sent." });
    }

    if (action === "complete_recovery") {
      const verifyResponse = await fetch(`${supabaseUrl}/auth/v1/verify`, {
        method: "POST",
        headers: {
          "apikey": publishableKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ type: "recovery", token, email }),
      });
      if (!verifyResponse.ok) {
        return jsonResponse({ error: "Invalid or expired recovery code." }, 400);
      }

      const recoverySession = await verifyResponse.json();
      const passwordResponse = await fetch(`${supabaseUrl}/auth/v1/user`, {
        method: "PUT",
        headers: {
          "apikey": publishableKey,
          "Authorization": `Bearer ${recoverySession.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });
      if (!passwordResponse.ok) {
        return jsonResponse({ error: "Could not update the password. Request a new recovery code." }, 400);
      }
      return jsonResponse({ message: "Password updated." });
    }

    const authResponse = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
      method: "POST",
      headers: {
        "apikey": publishableKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });
    const authPayload = await authResponse.json();
    if (!authResponse.ok) {
      return jsonResponse({ error: "Invalid username or password" }, 401);
    }

    return jsonResponse(authPayload);
  } catch {
    return jsonResponse({ error: "Authentication service unavailable" }, 503);
  }
});