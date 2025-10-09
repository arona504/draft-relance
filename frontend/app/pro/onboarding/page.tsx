import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { ProOnboardingClient } from "@/components/login/pro-onboarding-client";
import { authOptions } from "@/lib/auth";

const PRO_ROLES = new Set(["doctor", "nurse", "secretary", "clinic_admin"]);

export default async function ProOnboardingPage({ searchParams }: { searchParams: { token?: string } }) {
  const invitationToken = searchParams.token;
  if (!invitationToken) {
    redirect("/pro");
  }

  const session = await getServerSession(authOptions);
  if (!session) {
    redirect(`/pro?token=${encodeURIComponent(invitationToken)}`);
  }

  const roles = session.user?.roles ?? [];
  if (roles.some((role) => PRO_ROLES.has(role))) {
    redirect("/app/pro");
  }

  return <ProOnboardingClient token={invitationToken} />;
}
