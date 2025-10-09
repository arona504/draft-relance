import { getServerSession } from "next-auth";
import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";
import { authOptions } from "@/lib/auth";

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const secret = process.env.NEXTAUTH_SECRET;
  const token = await getToken({ req: request, secret });
  const accessToken = token?.accessToken;

  if (!accessToken || typeof accessToken !== "string") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!process.env.API_BASE) {
    return NextResponse.json({ error: "API_BASE is not configured" }, { status: 500 });
  }

  const payload = await request.json();
  const response = await fetch(`${process.env.API_BASE}/commands/scheduling/appointments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });

  let data: unknown;
  try {
    data = await response.json();
  } catch (error) {
    data = { error: "Invalid response from API" };
  }

  return NextResponse.json(data, { status: response.status });
}
