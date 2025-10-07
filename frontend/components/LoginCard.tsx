"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/button";

export function LoginCard() {
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    try {
      await signIn("keycloak", { callbackUrl: "/app" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl ring-1 ring-emerald-100">
      <div className="mb-6 space-y-2 text-center">
        <h1 className="text-2xl font-semibold text-emerald-900">Keur Doctor</h1>
        <p className="text-sm text-slate-600">
          Plateforme de prise de rendez-vous sécurisée pour les structures de santé sénégalaises.
        </p>
      </div>

      <div className="space-y-4">
        <Button className="w-full" onClick={handleLogin} disabled={loading}>
          {loading ? "Redirection vers Keycloak..." : "Se connecter avec Keycloak"}
        </Button>

        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
          <span className="h-px flex-1 bg-slate-200" />
          <span>ou</span>
          <span className="h-px flex-1 bg-slate-200" />
        </div>

        <form className="grid gap-3" onSubmit={(event) => event.preventDefault()}>
          <input
            type="text"
            placeholder="Identifiant"
            className="h-10 rounded-md border border-slate-200 px-3 text-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
            disabled
          />
          <input
            type="password"
            placeholder="Mot de passe"
            className="h-10 rounded-md border border-slate-200 px-3 text-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
            disabled
          />
          <Button type="submit" variant="outline" disabled>
            Connexion locale (désactivée)
          </Button>
        </form>
      </div>
    </div>
  );
}
