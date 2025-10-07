import NextAuth, { type DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    user?: DefaultSession["user"] & {
      roles: string[];
      tenantId?: string;
    };
  }

  interface User {
    roles?: string[];
    tenantId?: string;
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
  }
}
