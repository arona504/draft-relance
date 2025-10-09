import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { AppointmentForm } from "../components/AppointmentForm";
import { authOptions } from "@/lib/auth";

export default async function PatientDashboard() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.roles?.includes("patient")) {
    redirect("/patient");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-8 px-4 py-12">
      <header className="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-emerald-100">
        <div className="flex flex-col gap-2">
          <p className="text-sm text-slate-500">Bienvenue {session.user.name ?? ""}</p>
          <h1 className="text-2xl font-semibold text-emerald-900">Suivi de vos rendez-vous</h1>
          <p className="text-sm text-slate-600">
            Consultez vos prochains rendez-vous et facilitez vos partages avec vos clinques partenaires.
          </p>
        </div>
      </header>

      <section className="grid gap-4">
        <h2 className="text-lg font-semibold text-emerald-800">Réserver un créneau</h2>
        <AppointmentForm />
      </section>
    </main>
  );
}
