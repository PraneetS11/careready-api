import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fromZonedTime } from "date-fns-tz";
import { ArrowRight } from "lucide-react";
import { api, post } from "./api";
import { ErrorNotice } from "./ui";
import type { Agency, Catalog } from "./types";
export default function RequestForm({
  catalog,
  onDone,
}: {
  catalog: Catalog;
  onDone: () => void;
}) {
  const [city, setCity] = useState("Toronto");
  const [error, setError] = useState<unknown>();
  const [busy, setBusy] = useState(false);
  const cache = useQueryClient();
  const { data: agencies = [] } = useQuery({
    queryKey: ["agencies"],
    queryFn: () => api<Agency[]>("/network/agencies"),
  });
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError(undefined);
    const d = new FormData(e.currentTarget);
    try {
      await post("/network/visits", {
        agency_id: d.get("agency_id"),
        service: d.get("service"),
        recipient: d.get("recipient"),
        address: d.get("address"),
        city,
        starts_at: fromZonedTime(
          String(d.get("starts_at")),
          catalog.cities[city].timezone,
        ).toISOString(),
        duration_minutes: Number(d.get("duration_minutes")),
        min_experience: Number(d.get("min_experience")),
        occurrences: Number(d.get("occurrences")),
        gender_preference: d.get("gender_preference"),
        preferred_language: d.get("preferred_language"),
        communication: d.get("communication"),
        smoke_free: d.has("smoke_free"),
        pets_present: d.has("pets_present"),
        notes: d.get("notes"),
        consent_confirmed: d.has("consent_confirmed"),
      });
      await cache.invalidateQueries({ queryKey: ["visits"] });
      onDone();
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={submit} className="request-form">
      <p className="muted">
        Tell us what would make a good visit. Your agency will review the
        request before offering it to a provider.
      </p>
      <div className="form-section-label">
        01 <span>The essentials</span>
      </div>
      <div className="form-grid">
        <label>
          Who is receiving care?
          <input
            name="recipient"
            required
            minLength={2}
            maxLength={100}
            placeholder="Recipient’s name"
          />
        </label>
        <label>
          Service
          <select name="service">
            {Object.entries(catalog.services).map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label>
          City
          <select value={city} onChange={(e) => setCity(e.target.value)}>
            {Object.keys(catalog.cities).map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Care agency
          <select name="agency_id" required defaultValue="" key={city}>
            <option value="" disabled>
              Select an agency
            </option>
            {agencies
              .filter((a) => a.city === city)
              .map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
          </select>
        </label>
      </div>
      {!agencies.some((a) => a.city === city) && (
        <p className="notice">
          No verified agency serves this city yet. Try a city with an agency or
          register an agency first.
        </p>
      )}
      <label>
        Visit address
        <input
          name="address"
          required
          minLength={5}
          maxLength={250}
          placeholder="Street address and apartment"
        />
        <small>Only your agency and assigned provider can see this.</small>
      </label>
      <div className="form-section-label">
        02 <span>Time together</span>
      </div>
      <div className="form-grid">
        <label>
          First visit · {catalog.cities[city].timezone}
          <input type="datetime-local" name="starts_at" required />
        </label>
        <label>
          Duration
          <select name="duration_minutes">
            {[30, 60, 90, 120, 180, 240].map((n) => (
              <option value={n} key={n}>
                {n} minutes
              </option>
            ))}
          </select>
        </label>
        <label>
          Repeat
          <select name="occurrences">
            <option value="1">One-time visit</option>
            {[2, 4, 6, 8, 12].map((n) => (
              <option key={n} value={n}>
                Weekly · {n} visits
              </option>
            ))}
          </select>
        </label>
        <label>
          Minimum experience
          <select name="min_experience">
            {catalog.experience_levels.map((l, i) => (
              <option key={l} value={i}>
                {l}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="form-section-label">
        03 <span>Personal preferences</span>
      </div>
      <p className="hint">
        Preferences help providers understand your needs; they are not
        guaranteed matches.
      </p>
      <div className="form-grid">
        <label>
          Preferred language
          <select name="preferred_language">
            <option value="any">No preference</option>
            {catalog.languages.map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
        </label>
        <label>
          Provider gender
          <select name="gender_preference">
            <option value="any">No preference</option>
            <option value="woman">Woman</option>
            <option value="man">Man</option>
            <option value="nonbinary">Nonbinary</option>
          </select>
        </label>
        <label>
          Communication style
          <select name="communication">
            <option value="standard">No preference</option>
            <option value="slow_clear">Slow, clear communication</option>
            <option value="written">Written communication</option>
          </select>
        </label>
      </div>
      <div className="check-grid">
        <label className="check">
          <input type="checkbox" name="smoke_free" defaultChecked />
          Smoke-free visit preferred
        </label>
        <label className="check">
          <input type="checkbox" name="pets_present" />
          Pets in the home
        </label>
      </div>
      <label>
        Anything else to help the visit?
        <textarea
          name="notes"
          maxLength={1500}
          rows={3}
          placeholder="Access instructions or preferences. Use fictional details in this demo."
        />
      </label>
      <label className="check">
        <input type="checkbox" name="consent_confirmed" required />
        I’m requesting for myself or have permission to arrange support for this
        person.
      </label>
      <ErrorNotice error={error} />
      <button className="button primary" disabled={busy}>
        {busy ? "Sending request…" : "Send care request"}
        <ArrowRight size={17} />
      </button>
    </form>
  );
}
