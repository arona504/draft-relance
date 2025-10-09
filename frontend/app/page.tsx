import Link from "next/link";

const cards = [
  {
    title: "Espace Patient",
    description:
      "Prendre un rendez-vous, consulter vos prochains passages et gérer vos partages de dossier.",
    href: "/patient",
    cta: "Accéder à l'espace patient",
  },
  {
    title: "Espace Professionnel",
    description:
      "Gérer vos agendas, vos équipes et la coordination inter-structure (accès sur invitation).",
    href: "/pro",
    cta: "Accéder à l'espace professionnel",
  },
];

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-emerald-100 via-white to-sky-100 px-4 py-16">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8 text-center">
        <div className="space-y-3">
          <p className="text-sm font-medium uppercase tracking-[0.3em] text-emerald-600">Keur Doctor</p>
          <h1 className="text-3xl font-semibold sm:text-4xl">
            Choisissez votre espace sécurisé
          </h1>
          <p className="mx-auto max-w-2xl text-sm text-slate-600">
            Keur Doctor sépare les parcours patients et professionnels de santé pour offrir une expérience
            adaptée à chacun. Sélectionnez votre profil pour poursuivre la connexion.
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          {cards.map((card) => (
            <div
              key={card.href}
              className="rounded-2xl border border-emerald-200/60 bg-white/80 p-6 shadow-lg backdrop-blur transition hover:-translate-y-1 hover:shadow-xl"
            >
              <h2 className="text-xl font-semibold text-slate-900">{card.title}</h2>
              <p className="mt-3 text-sm text-slate-600">{card.description}</p>
              <Link
                href={card.href}
                className="mt-6 inline-flex w-full items-center justify-center rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                {card.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
