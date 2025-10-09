import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { authOptions } from "@/lib/auth";

const PRO_ROLES = new Set(["doctor", "nurse", "secretary", "clinic_admin"]);

export default async function ProDashboard() {
  const session = await getServerSession(authOptions);
  const roles = session?.user?.roles ?? [];
  if (!session?.user || !roles.some((role) => PRO_ROLES.has(role))) {
    redirect("/pro");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-6 px-4 py-12">
      <header className="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-emerald-100">
        <div className="flex flex-col gap-2">
          <p className="text-sm text-slate-500">Bienvenue {session.user.name ?? ""}</p>
          <h1 className="text-2xl font-semibold text-emerald-900">Console professionnelle</h1>
          <p className="text-sm text-slate-600">
            Gérez vos agendas, confirmez les rendez-vous et coordonnez vos équipes multi-tenant.
          </p>
        </div>
      </header>

      <section className="grid gap-4 rounded-xl border border-emerald-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-emerald-800">Accès rapides</h2>
        <ul className="grid gap-3 text-sm text-slate-600 md:grid-cols-2">
          <li className="rounded-lg border border-emerald-100 bg-emerald-50 p-4">
            Synchroniser les agendas et appliquer une politique de double validation.
          </li>
          <li className="rounded-lg border border-emerald-100 bg-emerald-50 p-4">
            Suivre les demandes patient et gérer les partages de dossier par tenant.
          </li>
          <li className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            Inviter un nouveau membre via un lien sécurisé (MFA obligatoire).
          </li>
          <li className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            Consulter les rapports d&apos;activité de votre clinique.
          </li>
        </ul>
      </section>
    </main>
  );
}
