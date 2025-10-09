import { getServerSession } from "next-auth";
import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

import { authOptions } from "@/lib/auth";

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const secret = process.env.NEXTAUTH_SECRET;
  const token = await getToken({ req: request, secret });
  const accessToken = token?.accessToken;

  if (!accessToken || typeof accessToken !== "string") {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  if (!process.env.API_BASE) {
    return NextResponse.json({ error: "API_BASE n'est pas configuré" }, { status: 500 });
  }

  const payload = await request.json();

  const response = await fetch(`${process.env.API_BASE}/commands/onboarding/pro-invitations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    return NextResponse.json(
      { error: typeof data === "object" && data && "detail" in data ? (data as Record<string, unknown>).detail : "Erreur lors de la génération de l'invitation" },
      { status: response.status },
    );
  }

  return NextResponse.json(data, { status: 201 });
}
