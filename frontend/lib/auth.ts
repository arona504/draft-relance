import { jwtDecode } from "jwt-decode";
import type { JWT } from "next-auth/jwt";
import type { NextAuthOptions } from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

const backendClientId = process.env.KEYCLOAK_BACKEND_CLIENT_ID ?? "keur-backend";
const tokenEndpoint = process.env.KEYCLOAK_TOKEN_ENDPOINT;

const PROVIDER_CONFIG = {
  "keycloak-patient": {
    clientId: process.env.KEYCLOAK_PATIENT_CLIENT_ID ?? "",
    clientSecret: process.env.KEYCLOAK_PATIENT_CLIENT_SECRET ?? "",
  },
  "keycloak-pro": {
    clientId: process.env.KEYCLOAK_PRO_CLIENT_ID ?? "",
    clientSecret: process.env.KEYCLOAK_PRO_CLIENT_SECRET ?? "",
  },
} as const;

const PRO_ROLE_SET = new Set(["doctor", "nurse", "secretary", "clinic_admin"]);

function decodeAccessToken(token: string, jwtToken: JWT): JWT {
  try {
    const decoded = jwtDecode<{ tenant_id?: string; tenantId?: string; preferred_username?: string; email?: string; resource_access?: Record<string, { roles?: string[] }>; roles?: string[] }>(token);
    const roles =
      decoded.resource_access?.[backendClientId]?.roles ??
      decoded.roles ??
      [];
    jwtToken.roles = Array.isArray(roles)
      ? roles.map((role) => role.toLowerCase())
      : [];
    jwtToken.tenantId = decoded.tenant_id ?? decoded.tenantId ?? jwtToken.tenantId;
    jwtToken.username = decoded.preferred_username ?? jwtToken.username ?? undefined;
    jwtToken.email = decoded.email ?? jwtToken.email ?? undefined;
  } catch (error) {
    console.warn("Failed to decode access token", error);
  }
  return jwtToken;
}

async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken || !tokenEndpoint) {
    return token;
  }

  const provider = (token.provider as keyof typeof PROVIDER_CONFIG) ?? "keycloak-patient";
  const config = PROVIDER_CONFIG[provider];
  if (!config?.clientId) {
    console.error(`Missing client configuration for provider ${provider}`);
    return token;
  }

  try {
    const body = new URLSearchParams({
      grant_type: "refresh_token",
      client_id: config.clientId,
      refresh_token: String(token.refreshToken),
    });
    if (config.clientSecret) {
      body.append("client_secret", config.clientSecret);
    }

    const response = await fetch(tokenEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });

    const refreshedTokens = await response.json();
    if (!response.ok) {
      throw refreshedTokens;
    }

    const nextToken: JWT = {
      ...token,
      accessToken: refreshedTokens.access_token,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
      expiresAt: Date.now() + (refreshedTokens.expires_in ?? 0) * 1000,
    };

    if (typeof nextToken.accessToken === "string") {
      return decodeAccessToken(nextToken.accessToken, nextToken);
    }

    return nextToken;
  } catch (error) {
    console.error("Failed to refresh access token", error);
    return { ...token, error: "RefreshAccessTokenError" as const };
  }
}

function buildKeycloakProvider(id: "keycloak-patient" | "keycloak-pro") {
  const config = PROVIDER_CONFIG[id];
  return KeycloakProvider({
    id,
    name: id === "keycloak-pro" ? "Compte Professionnel" : "Compte Patient",
    clientId: config.clientId,
    clientSecret: config.clientSecret,
    issuer: process.env.KEYCLOAK_ISSUER,
    checks: ["pkce", "state"],
    authorization: {
      params: {
        scope: "openid profile email offline_access",
      },
    },
  });
}

export const authOptions: NextAuthOptions = {
  providers: [buildKeycloakProvider("keycloak-patient"), buildKeycloakProvider("keycloak-pro")],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at ? account.expires_at * 1000 : undefined;
        token.provider = account.provider;
      }

      if (token.expiresAt && Date.now() >= token.expiresAt - 30_000) {
        token = await refreshAccessToken(token);
      }

      if (token.accessToken && typeof token.accessToken === "string") {
        token = decodeAccessToken(token.accessToken, token);
      }

      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.roles = Array.isArray(token.roles) ? token.roles : [];
        session.user.tenantId = typeof token.tenantId === "string" ? token.tenantId : undefined;
        session.user.name = token.username ?? session.user.name ?? undefined;
        session.user.type = session.user.roles?.some((role) => PRO_ROLE_SET.has(role)) ? "pro" : "patient";
      }
      session.provider = typeof token.provider === "string" ? token.provider : undefined;
      return session;
    },
  },
  pages: {
    signIn: "/patient",
  },
};
