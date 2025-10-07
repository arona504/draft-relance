import { withAuth } from "next-auth/middleware";

export default withAuth({
  callbacks: {
    authorized: ({ req, token }) => {
      if (!token) {
        return false;
      }

      const pathname = req.nextUrl.pathname;
      if (pathname.startsWith("/app/admin")) {
        const roles = Array.isArray(token.roles) ? token.roles : [];
        return roles.includes("clinic_admin");
      }

      return true;
    },
  },
});

export const config = {
  matcher: ["/app/:path*"],
};
