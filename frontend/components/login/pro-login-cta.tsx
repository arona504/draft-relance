"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const proProviderId = "keycloak-pro";

interface Props {
  requestAccessHref?: string;
  invitationToken?: string;
}

export function ProLoginCTA({ requestAccessHref, invitationToken }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const callbackUrl = invitationToken
        ? `/pro/onboarding?token=${encodeURIComponent(invitationToken)}`
        : "/app/pro";

      const response = await signIn(proProviderId, {
        callbackUrl,
        redirect: false,
      });
      if (response?.error) {
        setError("La connexion a échoué. Contactez votre administrateur.");
        setLoading(false);
        return;
      }
      if (response?.url) {
        window.location.href = response.url;
        return;
      }
    } catch (err) {
      console.error(err);
      setError("Service d'authentification indisponible.");
    }
    setLoading(false);
  };

  return (
    <div className="w-full max-w-[420px] space-y-8 px-6 sm:px-12">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-sky-600">Espace professionnel</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-foreground">Accès sécurisé aux outils de coordination</h2>
        <p className="mt-3 text-sm text-muted-foreground">
          L&apos;espace professionnel Keur Doctor est accessible sur invitation. MFA obligatoire pour sécuriser vos données patients.
        </p>
      </div>
      <Card className="border-border/50 shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl">Connexion avec Keycloak</CardTitle>
          <CardDescription>Authentifiez-vous avec vos identifiants professionnels fournis par votre clinique.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {invitationToken ? (
            <div className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              Invitation détectée. Connectez-vous pour finaliser votre rattachement à la clinique.
            </div>
          ) : null}
          <Button type="button" className="h-11 w-full" onClick={handleLogin} disabled={loading}>
            {loading ? "Redirection en cours..." : "Se connecter (Professionnel)"}
          </Button>

          {error ? (
            <div className="rounded-md border border-destructive/70 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <Separator className="bg-border" />

          <div className="space-y-3 text-sm text-muted-foreground">
            <p>MFA (TOTP / SMS / WebAuthn) requis pour accéder à votre tenant clinique.</p>
            <p>
              Vous n&apos;avez pas encore d&apos;accès ?
              {" "}
              {requestAccessHref ? (
                <a className="font-medium text-emerald-700 hover:underline" href={requestAccessHref}>Demander une invitation</a>
              ) : (
                <span className="font-medium text-emerald-700">Contactez l&apos;administrateur de votre clinique.</span>
              )}
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex-col items-start gap-2 text-sm text-muted-foreground">
          <p>Pour des raisons de sécurité, n&apos;utilisez pas de poste partagé sans vous déconnecter.</p>
          <p className="text-xs">© {new Date().getFullYear()} Keur Doctor</p>
        </CardFooter>
      </Card>
    </div>
  );
}
