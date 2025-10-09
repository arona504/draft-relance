import { getServerSession } from "next-auth";
import Image from "next/image";
import { redirect } from "next/navigation";

import { ProLoginCTA } from "@/components/login/pro-login-cta";
import { authOptions } from "@/lib/auth";

const PRO_ROLES = new Set(["doctor", "nurse", "secretary", "clinic_admin"]);

export default async function ProEntryPage({
  searchParams,
}: {
  searchParams: { token?: string };
}) {
  const session = await getServerSession(authOptions);
  const roles = session?.user?.roles ?? [];
  if (roles.some((role) => PRO_ROLES.has(role))) {
    redirect("/app/pro");
  }

  const invitationToken = searchParams?.token;

  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden bg-slate-900 lg:flex">
        <Image
          src="/login-pattern.svg"
          alt="Illustration onboarding professionnel"
          fill
          priority
          sizes="100vw"
          className="object-cover opacity-20"
        />
        <div className="relative z-10 flex flex-1 flex-col justify-between p-10 text-white">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-white/90 ring-1 ring-white/30">
              Professionnels de santé
            </span>
            <h1 className="mt-8 text-4xl font-semibold leading-tight">Coordonnez vos équipes et vos patients en toute sécurité.</h1>
            <p className="mt-6 max-w-md text-sm text-white/80">
              Gestion des agendas, coopération inter-cliniques et partage de dossiers avec authentification multi-facteur.
            </p>
          </div>
          <blockquote className="space-y-4 text-white/80">
            <p className="text-lg font-semibold text-white">“Nous avons uniformisé nos parcours de prise en charge multi-site grâce à Keur Doctor.”</p>
            <footer className="text-sm text-white/70">Pr Franck Niang — Direction médicale Dakar Nord</footer>
          </blockquote>
        </div>
      </div>
      <div className="flex items-center justify-center py-12">
        <ProLoginCTA
          requestAccessHref="mailto:support@keurdoctor.com?subject=Demande%20d%27acc%C3%A8s%20professionnel"
          invitationToken={invitationToken}
        />
      </div>
    </main>
  );
}
