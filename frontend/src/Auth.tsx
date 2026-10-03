import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { motion } from "motion/react";
import { api, post, setTokens } from "./api";
import type { Agency, Catalog, Role } from "./types";
import { Brand, ErrorNotice } from "./ui";
export default function Auth({
  mode = "login",
}: {
  mode?: "login" | "signup" | "forgot" | "reset" | "verify";
}) {
  const [role, setRole] = useState<Role>("requester");
  const [error, setError] = useState<unknown>();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const navigate = useNavigate();
  const { token } = useParams();
  const { data: agencies = [] } = useQuery({
    queryKey: ["agencies"],
    queryFn: () => api<Agency[]>("/network/agencies"),
  });
  const { data: catalog } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => api<Catalog>("/network/catalog"),
  });
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(undefined);
    setBusy(true);
    const form = e.currentTarget;
    const d = new FormData(form);
    try {
      const credentials = {
        email: d.get("email"),
        password: d.get("password"),
      };
      if (mode === "login") {
        const pair = await post<{
          access_token: string;
          refresh_token: string;
        }>("/auth/login", credentials);
        setTokens(pair);
        navigate("/app");
      } else if (mode === "signup") {
        const result = await post<{ verification_queued: boolean }>(
          "/network/register",
          {
            ...credentials,
            role,
            name: d.get("name"),
            agency_name: d.get("agency_name") || "",
            city: d.get("city") || "Toronto",
            agency_id: d.get("agency_id") || null,
            experience: Number(d.get("experience") || 0),
            gender: d.get("gender") || "undisclosed",
            services: d.getAll("services"),
            languages: d.getAll("languages").length
              ? d.getAll("languages")
              : ["English"],
          },
        );
        setMessage(
          result.verification_queued
            ? "Your account is ready. Open the verification email in the local mailbox, then sign in."
            : "Your account was created, but the email could not be queued. Sign in and request another verification email.",
        );
      } else if (mode === "forgot") {
        await post("/auth/password-reset-request", { email: d.get("email") });
        setMessage(
          "If that account exists, reset instructions are in the local mailbox.",
        );
      } else if (mode === "reset") {
        await post("/auth/password-reset-confirm/" + token, {
          password: d.get("password"),
          password_confirm: d.get("password_confirm"),
        });
        setMessage("Password updated. You can sign in with your new password.");
      } else {
        await api("/auth/verify/" + token);
        setMessage("Your email is verified. You can now sign in.");
      }
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }
  const title =
    mode === "signup"
      ? "A little care.\nA real connection."
      : mode === "login"
        ? "Good care starts\nwith people."
        : mode === "verify"
          ? "One last step."
          : mode === "reset"
            ? "A fresh start."
            : "Let’s get you back.";
  return (
    <main className="auth-layout">
      <section className="auth-story">
        <Link to="/login" aria-label="CareReady home">
          <Brand />
        </Link>
        <motion.div
          className="story-body"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p className="eyebrow">CARE, CONNECTED</p>
          <h1>{title}</h1>
          <p className="story-copy">
            Support at home. People you can count on. A calmer way to bring it
            all together.
          </p>
          <div className="care-art" aria-hidden="true">
            <div className="art-circle c-one" />
            <div className="art-circle c-two" />
            <div className="art-circle c-three" />
            <span className="art-note">
              Close to home.
              <br />
              <em>Connected by care.</em>
            </span>
            <span className="art-cross">+</span>
          </div>
        </motion.div>
        <div className="story-footer">
          <span>Built around people, not paperwork.</span>
          <ArrowUpRight size={20} />
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-top">
          <span>LOCAL PREVIEW</span>
          <a href="http://127.0.0.1:8029" target="_blank" rel="noreferrer">
            Open test mailbox <ArrowUpRight size={13} />
          </a>
        </div>
        <div className="auth-form-wrap">
          <p className="eyebrow">
            {mode === "signup"
              ? "FIND YOUR PLACE"
              : mode === "login"
                ? "WELCOME BACK"
                : "YOUR ACCOUNT"}
          </p>
          <h2>
            {mode === "signup"
              ? "Join the network"
              : mode === "login"
                ? "Sign in to CareReady"
                : mode === "verify"
                  ? "Verify your email"
                  : mode === "reset"
                    ? "Choose a new password"
                    : "Forgot your password?"}
          </h2>
          <p className="muted">
            {mode === "signup"
              ? "Choose how you’ll be part of someone’s day."
              : mode === "login"
                ? "Your people, visits and next steps—all in one place."
                : mode === "verify"
                  ? "Confirm this email belongs to you to activate your account."
                  : "We’ll help you get back to your workspace."}
          </p>
          {message ? (
            <div className="success-panel">
              <ShieldCheck size={32} />
              <h3>{message}</h3>
              <Link className="button primary" to="/login">
                Back to sign in <ArrowRight size={16} />
              </Link>
            </div>
          ) : (
            <form onSubmit={submit}>
              {mode === "signup" && (
                <>
                  <div className="role-options" aria-label="Account type">
                    {(["requester", "provider", "agency"] as Role[]).map(
                      (r) => (
                        <button
                          key={r}
                          type="button"
                          aria-pressed={role === r}
                          className={role === r ? "selected" : ""}
                          onClick={() => setRole(r)}
                        >
                          {r === "requester"
                            ? "I need care"
                            : r === "provider"
                              ? "I provide care"
                              : "I run an agency"}
                          {role === r && <Check size={13} />}
                        </button>
                      ),
                    )}
                  </div>
                  <label>
                    Your name
                    <input
                      name="name"
                      required
                      minLength={2}
                      maxLength={100}
                      autoComplete="name"
                      placeholder="Alex Morgan"
                    />
                  </label>
                </>
              )}
              {(mode === "login" || mode === "signup" || mode === "forgot") && (
                <label>
                  Email address
                  <input
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    placeholder="you@example.com"
                  />
                </label>
              )}
              {(mode === "login" || mode === "signup" || mode === "reset") && (
                <label>
                  Password
                  <input
                    name="password"
                    type="password"
                    required
                    minLength={6}
                    autoComplete={
                      mode === "login" ? "current-password" : "new-password"
                    }
                    placeholder="At least 6 characters"
                  />
                </label>
              )}
              {mode === "reset" && (
                <label>
                  Confirm password
                  <input
                    name="password_confirm"
                    type="password"
                    required
                    minLength={6}
                    autoComplete="new-password"
                  />
                </label>
              )}
              {mode === "signup" && role === "agency" && (
                <div className="form-grid">
                  <label>
                    Agency name
                    <input
                      name="agency_name"
                      required
                      minLength={2}
                      maxLength={100}
                      placeholder="Your care agency"
                    />
                  </label>
                  <label>
                    City
                    <select name="city">
                      {Object.keys(catalog?.cities || { Toronto: {} }).map(
                        (c) => (
                          <option key={c}>{c}</option>
                        ),
                      )}
                    </select>
                  </label>
                </div>
              )}
              {mode === "signup" && role === "provider" && (
                <>
                  <label>
                    Agency
                    <select name="agency_id" required defaultValue="">
                      <option value="" disabled>
                        Select your agency
                      </option>
                      {agencies.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} · {a.city}
                        </option>
                      ))}
                    </select>
                  </label>
                  {agencies.length === 0 && (
                    <p className="hint">
                      An agency must register and verify its email before
                      providers can join.
                    </p>
                  )}
                  <div className="form-grid">
                    <label>
                      Experience
                      <select name="experience">
                        {catalog?.experience_levels.map((l, i) => (
                          <option key={l} value={i}>
                            {l}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Gender · optional
                      <select name="gender">
                        <option value="undisclosed">Prefer not to say</option>
                        <option value="woman">Woman</option>
                        <option value="man">Man</option>
                        <option value="nonbinary">Nonbinary</option>
                      </select>
                    </label>
                  </div>
                  <fieldset>
                    <legend>Services you provide</legend>
                    <div className="check-grid">
                      {Object.entries(catalog?.services || {}).map(
                        ([id, name]) => (
                          <label key={id} className="check">
                            <input type="checkbox" name="services" value={id} />
                            {name}
                          </label>
                        ),
                      )}
                    </div>
                  </fieldset>
                  <fieldset>
                    <legend>Languages you speak</legend>
                    <div className="check-grid">
                      {catalog?.languages.map((l) => (
                        <label key={l} className="check">
                          <input
                            type="checkbox"
                            name="languages"
                            value={l}
                            defaultChecked={l === "English"}
                          />
                          {l}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  <p className="hint">
                    Your agency reviews your profile before you can accept
                    visits.
                  </p>
                </>
              )}
              <ErrorNotice error={error} />
              <button className="button primary auth-submit" disabled={busy}>
                {busy
                  ? "Please wait…"
                  : mode === "signup"
                    ? "Create account"
                    : mode === "login"
                      ? "Sign in"
                      : mode === "verify"
                        ? "Verify email"
                        : mode === "reset"
                          ? "Update password"
                          : "Send reset link"}
                <ArrowRight size={17} />
              </button>
            </form>
          )}
          {!message && (
            <div className="auth-links">
              {mode === "login" ? (
                <>
                  <Link to="/forgot">Forgot password?</Link>
                  <span>
                    New here? <Link to="/signup">Create an account</Link>
                  </span>
                </>
              ) : (
                <Link to="/login">Already have an account? Sign in</Link>
              )}
            </div>
          )}
          <div className="auth-footnote">
            <Mail size={15} />
            <span>
              Demo emails stay in the local mailbox. Use fictional information.
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}
