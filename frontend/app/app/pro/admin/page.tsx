import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";

export default async function AdminPage() {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect("/pro");
  }

  const roles = session.user.roles ?? [];
  if (!roles.includes("clinic_admin")) {
    redirect("/app/pro");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-4 py-12">
      <header className="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-emerald-100">
        <h1 className="text-2xl font-semibold text-emerald-900">Espace administrateur</h1>
        <p className="mt-2 text-sm text-slate-600">
          Gestion des agendas, validation des grilles et revue des accès inter-tenant.
        </p>
      </header>
      <section className="rounded-xl border border-emerald-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-emerald-800">Prochaines étapes</h2>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-600">
          <li>Configurer les agendas des praticiens.</li>
          <li>Valider les règles de partage de dossier inter-tenant.</li>
          <li>Superviser la capacité des créneaux et les équipes.</li>
        </ul>
      </section>
    </main>
  );
}
