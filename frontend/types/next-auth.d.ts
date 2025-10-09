import NextAuth, { type DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    provider?: string;
    user?: DefaultSession["user"] & {
      roles: string[];
      tenantId?: string;
      type?: "patient" | "pro";
    };
  }

  interface User {
    roles?: string[];
    tenantId?: string;
    type?: "patient" | "pro";
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    expiresAt?: number;
    roles?: string[];
    tenantId?: string;
    username?: string;
    error?: string;
    provider?: string;
    email?: string;
  }
}
