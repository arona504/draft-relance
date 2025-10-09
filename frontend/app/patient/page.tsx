import { getServerSession } from "next-auth";
import Image from "next/image";
import { redirect } from "next/navigation";

import { PatientLoginCTA } from "@/components/login/patient-login-cta";
import { authOptions } from "@/lib/auth";

export default async function PatientEntryPage() {
  const session = await getServerSession(authOptions);
  if (session?.user?.roles?.includes("patient")) {
    redirect("/app/patient");
  }

  const issuer = process.env.KEYCLOAK_ISSUER ?? "";
  const clientId = process.env.KEYCLOAK_PATIENT_CLIENT_ID ?? "";
  const baseUrl = process.env.NEXTAUTH_URL ?? "http://localhost:3000";
  const registrationUrl = issuer && clientId
    ? `${issuer}/protocol/openid-connect/registrations?client_id=${clientId}&response_type=code&scope=openid%20profile%20email&redirect_uri=${encodeURIComponent(`${baseUrl}/api/auth/callback/keycloak-patient`)}`
    : "#";

  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden bg-emerald-700 lg:flex">
        <Image
          src="/login-pattern.svg"
          alt="Illustration Keur Doctor"
          fill
          priority
          sizes="100vw"
          className="object-cover opacity-30"
        />
        <div className="relative z-10 flex flex-1 flex-col justify-between p-10 text-white">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-white/90 ring-1 ring-white/30">
              Espace patient
            </span>
            <h1 className="mt-8 text-4xl font-semibold leading-tight">Suivez vos rendez-vous et vos partages en un clin d&apos;oeil.</h1>
            <p className="mt-6 max-w-md text-sm text-white/80">
              Connectez-vous pour réserver une consultation, partager un dossier médical avec une clinique ou
              retrouver l&apos;historique de vos soins.
            </p>
          </div>
          <blockquote className="space-y-4 text-white/80">
            <p className="text-lg font-semibold text-white">“Un vrai gain de temps pour prendre un rendez-vous et suivre mes résultats.”</p>
            <footer className="text-sm text-white/70">Aminata — Patiente Dakar</footer>
          </blockquote>
        </div>
      </div>
      <div className="flex items-center justify-center py-12">
        <PatientLoginCTA registrationUrl={registrationUrl} />
      </div>
    </main>
  );
}
