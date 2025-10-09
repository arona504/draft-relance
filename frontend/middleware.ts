import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

const PRO_ROLES = new Set(["doctor", "nurse", "secretary", "clinic_admin"]);

export default withAuth(
  function middleware(req) {
    const token = req.nextauth.token;
    const url = req.nextUrl.clone();
    const pathname = url.pathname;

    const redirectTo = (path: string) => NextResponse.redirect(new URL(path, req.url));

    if (!token) {
      if (pathname.startsWith("/app/pro")) {
        return redirectTo("/pro");
      }
      return redirectTo("/patient");
    }

    const roles = Array.isArray(token.roles) ? token.roles.map((role) => String(role).toLowerCase()) : [];

    if (pathname.startsWith("/app/patient")) {
      if (roles.includes("patient")) {
        return NextResponse.next();
      }
      return redirectTo("/patient");
    }

    if (pathname.startsWith("/app/pro/admin")) {
      if (roles.includes("clinic_admin")) {
        return NextResponse.next();
      }
      return redirectTo("/pro");
    }

    if (pathname.startsWith("/app/pro")) {
      if (roles.some((role) => PRO_ROLES.has(role))) {
        return NextResponse.next();
      }
      return redirectTo("/pro");
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: () => true,
    },
  },
);

export const config = {
  matcher: ["/app/:path*"],
};
