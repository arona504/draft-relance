"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export function ProOnboardingClient({ token }: { token: string }) {
  const router = useRouter();
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  const acceptInvitation = async () => {
    setStatus("loading");
    setMessage(null);
    const response = await fetch("/api/bff/pro/invitations/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      setMessage(body?.error ?? "Impossible de valider l'invitation.");
      setStatus("error");
      return;
    }

    setStatus("success");
    setMessage("Invitation validée. Veuillez relancer votre session pour voir vos nouveaux accès.");
    setTimeout(() => router.replace("/app/pro"), 2000);
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-900/5 px-4 py-12">
      <Card className="w-full max-w-xl border-border/60 shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl">Finaliser votre invitation</CardTitle>
          <CardDescription>
            Confirmez votre invitation pour rattacher votre compte à la clinique et obtenir vos rôles professionnels.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3 text-sm text-muted-foreground">
            <p>
              Cette étape associe votre compte Keycloak au tenant indiqué dans l&apos;invitation et applique le rôle
              défini par votre administrateur.
            </p>
            <p>
              Assurez-vous d&apos;avoir terminé le parcours MFA demandé par votre clinique avant de confirmer.
            </p>
          </div>
          <Separator className="bg-border" />
          {message ? (
            <div
              className={`rounded-md border px-3 py-2 text-sm ${status === "success" ? "border-emerald-300 bg-emerald-50 text-emerald-700" : "border-destructive/70 bg-destructive/10 text-destructive"}`}
            >
              {message}
            </div>
          ) : null}
          <Button onClick={acceptInvitation} disabled={status === "loading" || status === "success"}>
            {status === "loading" ? "Validation en cours..." : "Valider l&apos;invitation"}
          </Button>
        </CardContent>
        <CardFooter className="text-xs text-muted-foreground">
          En cas d&apos;erreur, contactez l&apos;administrateur qui vous a invité pour obtenir un nouveau lien.
        </CardFooter>
      </Card>
    </main>
  );
}
