"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  defaultMode?: "onsite" | "tele";
}

export function AppointmentForm({ defaultMode = "onsite" }: Props) {
  const [slotId, setSlotId] = useState("");
  const [patientId, setPatientId] = useState("");
  const [mode, setMode] = useState<"onsite" | "tele" | "">(defaultMode);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/api/bff/appointments", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ slot_id: slotId, patient_id: patientId, mode: mode || undefined }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(typeof data?.error === "string" ? data.error : "Impossible de créer le rendez-vous");
      } else {
        setMessage("Rendez-vous créé ! ID: " + (data.appointment_id ?? "?"));
        setSlotId("");
        setPatientId("");
      }
    } catch (err) {
      setError("Erreur réseau");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-emerald-100 bg-white p-6 shadow-sm">
      <div>
        <label className="text-sm font-medium text-slate-700">Slot ID</label>
        <input
          value={slotId}
          onChange={(event) => setSlotId(event.target.value)}
          required
          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
        />
      </div>
      <div>
        <label className="text-sm font-medium text-slate-700">Patient ID</label>
        <input
          value={patientId}
          onChange={(event) => setPatientId(event.target.value)}
          required
          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
        />
      </div>
      <div>
        <label className="text-sm font-medium text-slate-700">Mode</label>
        <select
          value={mode}
          onChange={(event) => setMode(event.target.value as typeof mode)}
          className="mt-1 w-full rounded-md border border-slate-200 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-100"
        >
          <option value="">Choisir...</option>
          <option value="onsite">Présentiel</option>
          <option value="tele">Téléconsultation</option>
        </select>
      </div>
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "En cours..." : "Réserver"}
      </Button>
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  );
}
