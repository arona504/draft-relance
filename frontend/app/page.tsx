import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { LoginCard } from "@/components/LoginCard";
import { authOptions } from "@/lib/auth";

export default async function Home() {
  const session = await getServerSession(authOptions);
  if (session) {
    redirect("/app");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-tr from-emerald-200 via-white to-emerald-50 p-4">
      <LoginCard />
    </main>
  );
}
