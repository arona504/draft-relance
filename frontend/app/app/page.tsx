import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";

export default async function Dashboard() {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect("/patient");
  }

  const roles = session.user.roles ?? [];
  if (roles.includes("patient")) {
    redirect("/app/patient");
  }
  if (roles.some((role) => ["doctor", "nurse", "secretary", "clinic_admin"].includes(role))) {
    redirect("/app/pro");
  }

  redirect("/patient");
}
