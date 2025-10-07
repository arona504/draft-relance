import { jwtDecode } from "jwt-decode";
import type { JWT } from "next-auth/jwt";
import type { NextAuthOptions } from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

type KeycloakAccessToken = {
  sub: string;
  tenant_id?: string;
  preferred_username?: string;
  resource_access?: Record<string, { roles?: string[] }>;
};

const backendClientId = process.env.KEYCLOAK_BACKEND_CLIENT_ID ?? "keur-backend";
const tokenEndpoint = process.env.KEYCLOAK_TOKEN_ENDPOINT;

function decodeAccessToken(token: string, jwtToken: JWT): JWT {
  try {
    const decoded = jwtDecode<KeycloakAccessToken>(token);
    jwtToken.roles = decoded.resource_access?.[backendClientId]?.roles ?? [];
    jwtToken.tenantId = decoded.tenant_id;
    jwtToken.username = decoded.preferred_username;
  } catch (error) {
    console.warn("Failed to decode access token", error);
  }
  return jwtToken;
}

async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken || !tokenEndpoint) {
    return token;
  }

  try {
    const response = await fetch(tokenEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: process.env.KEYCLOAK_CLIENT_ID ?? "",
        client_secret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
        refresh_token: token.refreshToken as string,
      }),
    });

    const refreshed = await response.json();
    if (!response.ok) {
      throw refreshed;
    }

    const nextToken: JWT = {
      ...token,
      accessToken: refreshed.access_token,
      refreshToken: refreshed.refresh_token ?? token.refreshToken,
      expiresAt: Date.now() + (refreshed.expires_in ?? 0) * 1000,
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

export const authOptions: NextAuthOptions = {
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_CLIENT_ID ?? "",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
      issuer: process.env.KEYCLOAK_ISSUER,
      authorization: {
        params: {
          scope: "openid profile email offline_access",
        },
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.expiresAt = account.expires_at ? account.expires_at * 1000 : undefined;
      }

      if (token.expiresAt && Date.now() > token.expiresAt - 30_000) {
        token = await refreshAccessToken(token);
      }

      if (token.accessToken && typeof token.accessToken === "string") {
        token = decodeAccessToken(token.accessToken, token);
      }

      return token;
    },
    async session({ session, token }) {
      if (token?.accessToken && typeof token.accessToken === "string") {
        session.accessToken = token.accessToken;
      }
      if (session.user) {
        session.user.roles = Array.isArray(token.roles) ? token.roles : [];
        session.user.tenantId = typeof token.tenantId === "string" ? token.tenantId : undefined;
        session.user.name = token.username ?? session.user.name ?? undefined;
      }
      return session;
    },
  },
  pages: {
    signIn: "/",
  },
};
