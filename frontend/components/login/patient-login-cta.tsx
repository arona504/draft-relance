"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

const patientProviderId = "keycloak-patient";

type Props = {
  registrationUrl: string;
};

export function PatientLoginCTA({ registrationUrl }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await signIn(patientProviderId, {
        callbackUrl: "/app/patient",
        redirect: false,
      });
      if (response?.error) {
        setError("La connexion a échoué. Veuillez réessayer.");
        setLoading(false);
        return;
      }
      if (response?.url) {
        window.location.href = response.url;
        return;
      }
    } catch (err) {
      console.error(err);
      setError("Impossible de joindre le service d'authentification.");
    }
    setLoading(false);
  };

  return (
    <div className="w-full max-w-[420px] space-y-8 px-6 sm:px-12">
      <div>
        <p className="text-sm font-medium uppercase tracking-[0.24em] text-emerald-600">Espace patient</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-foreground">Connectez-vous ou créez un compte</h2>
        <p className="mt-3 text-sm text-muted-foreground">
          Keur Doctor vous permet de réserver une consultation et partager vos documents médicaux avec votre équipe soignante.
        </p>
      </div>
      <Card className="border-border/50 shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl">Connexion sécurisée</CardTitle>
          <CardDescription>Utilisez votre compte Keycloak pour accéder à votre espace patient.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <form className="space-y-4" onSubmit={(event) => event.preventDefault()}>
            <div className="space-y-2">
              <Label className="text-sm font-medium" htmlFor="patient-email">Adresse e-mail</Label>
              <Input id="patient-email" type="email" placeholder="prenom.nom@example.com" disabled />
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium" htmlFor="patient-password">Mot de passe</Label>
              <Input id="patient-password" type="password" placeholder="••••••••" disabled />
            </div>
            <Button type="button" className="h-11 w-full" onClick={handleLogin} disabled={loading}>
              {loading ? "Connexion en cours..." : "Se connecter avec Keycloak"}
            </Button>
          </form>

          {error ? (
            <div className="rounded-md border border-destructive/70 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          ) : null}

          <Separator className="bg-border" />

          <div className="space-y-3 text-sm text-muted-foreground">
            <p>Pas encore de compte ? Créez-le en quelques instants pour réserver vos prochains rendez-vous.</p>
            <a
              className="inline-flex items-center justify-center rounded-md border border-emerald-200 px-4 py-2 text-sm font-medium text-emerald-700 transition hover:bg-emerald-50"
              href={registrationUrl}
            >
              Créer un compte patient
            </a>
          </div>
        </CardContent>
        <CardFooter className="flex-col items-start gap-2 text-sm text-muted-foreground">
          <p>Les données sont hébergées de manière sécurisée et conformes à la réglementation en vigueur.</p>
          <p className="text-xs">© {new Date().getFullYear()} Keur Doctor</p>
        </CardFooter>
      </Card>
    </div>
  );
}
