"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export function LoginCard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await signIn("keycloak", {
        callbackUrl: "/app",
        redirect: false,
      });

      if (response?.error) {
        setError(
          "La connexion a échoué, veuillez réessayer ou contacter l'administrateur."
        );
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
      setLoading(false);
      return;
    }

    setLoading(false);
  };

  return (
    <Card className="border-border/50 shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl">Accéder à votre espace</CardTitle>
        <CardDescription>
          Authentifiez-vous avec votre compte Keur Doctor.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <form
          className="space-y-4"
          onSubmit={(event) => event.preventDefault()}
        >
          <div className="space-y-2">
            <Label htmlFor="email">Adresse e-mail</Label>
            <Input
              id="email"
              type="email"
              placeholder="prenom.nom@structure.sn"
              disabled
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Mot de passe</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              disabled
            />
          </div>
          <Button
            type="button"
            className="w-full"
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? "Connexion en cours..." : "Se connecter avec Keycloak"}
          </Button>
        </form>

        {error ? (
          <div className="rounded-md border border-destructive/80 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        <Separator className="bg-border" />

        <div className="space-y-3 text-sm text-muted-foreground">
          <p>
            La connexion locale est désactivée. Utilisez votre compte Keycloak
            fourni par l&apos;administrateur de votre structure pour accéder à
            l&apos;application multi-tenant.
          </p>
          <p>
            Besoin d&apos;aide ? Contactez le support Keur Doctor pour recevoir vos
            identifiants ou une invitation.
          </p>
        </div>
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm text-muted-foreground">
        <p>
          En vous connectant, vous acceptez les politiques de sécurité et de
          confidentialité de votre structure.
        </p>
        <p className="text-xs">
          © {new Date().getFullYear()} Keur Doctor. Tous droits réservés.
        </p>
      </CardFooter>
    </Card>
  );
}
