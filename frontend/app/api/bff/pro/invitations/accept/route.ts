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

  const body = await request.json();
  if (!body?.token) {
    return NextResponse.json({ error: "Token d'invitation manquant" }, { status: 400 });
  }

  if (!process.env.API_BASE) {
    return NextResponse.json({ error: "API_BASE n'est pas configuré" }, { status: 500 });
  }

  const response = await fetch(`${process.env.API_BASE}/commands/onboarding/pro-invitations/accept`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ token: body.token }),
  });

  let data: unknown;
  try {
    data = await response.json();
  } catch {
    data = undefined;
  }

  if (!response.ok) {
    return NextResponse.json(
      { error: typeof data === "object" && data && "detail" in data ? (data as Record<string, unknown>).detail : "Erreur lors de la validation de l'invitation" },
      { status: response.status },
    );
  }

  return NextResponse.json(data ?? { status: "ok" }, { status: 200 });
}
