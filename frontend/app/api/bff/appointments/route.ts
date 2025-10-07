import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "@/lib/auth";

export async function POST(request: Request) {
  const session = await getServerSession(authOptions);

  if (!session?.accessToken) {
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
      Authorization: `Bearer ${session.accessToken}`,
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
