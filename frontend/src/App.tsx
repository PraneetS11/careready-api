import { lazy, Suspense, useState } from "react";
import {
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  ArrowUpRight,
  CalendarDays,
  CircleHelp,
  Globe2,
  LayoutDashboard,
  LogOut,
  MapPin,
  Plus,
  Search,
  Users,
  Package,
  ArrowRight,
  Check,
  Clock3,
  Menu,
  X,
  Mail,
} from "lucide-react";
import Auth from "./Auth";
import RequestForm from "./RequestForm";
import { api, logout, patch, post, signedIn } from "./api";
import type { Account, Catalog, Device, TeamMember, Visit } from "./types";
import {
  Brand,
  Counter,
  Empty,
  ErrorNotice,
  Modal,
  PageTitle,
  Primary,
  Status,
} from "./ui";
const Globe = lazy(() => import("./Globe"));
const friendly = (text: string) => text.replaceAll("_", " ");
function date(v: Visit) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: v.timezone,
    timeZoneName: "short",
  }).format(new Date(v.starts_at));
}
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Auth key="login" />} />
      <Route path="/signup" element={<Auth key="signup" mode="signup" />} />
      <Route path="/forgot" element={<Auth key="forgot" mode="forgot" />} />
      <Route path="/reset/:token" element={<Auth key="reset" mode="reset" />} />
      <Route
        path="/verify/:token"
        element={<Auth key="verify" mode="verify" />}
      />
      <Route path="/app/*" element={<Workspace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
function Workspace() {
  const location = useLocation();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [mobile, setMobile] = useState(false);
  const [newRequest, setNewRequest] = useState(false);
  const [selected, setSelected] = useState<Visit | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [notice, setNotice] = useState("");
  const { data: me, error: accountError } = useQuery({
    queryKey: ["account"],
    queryFn: () => api<Account>("/network/me"),
    enabled: signedIn(),
  });
  const { data: catalog } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => api<Catalog>("/network/catalog"),
  });
  const enabled = !!me?.is_verified;
  const visitsQuery = useQuery({
    queryKey: ["visits"],
    queryFn: () => api<Visit[]>("/network/visits"),
    enabled,
    refetchInterval: 30000,
  });
  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api<Visit[]>("/network/jobs"),
    enabled: enabled && me?.role === "provider",
    refetchInterval: 30000,
  });
  const teamQuery = useQuery({
    queryKey: ["team"],
    queryFn: () => api<TeamMember[]>("/network/team"),
    enabled: enabled && me?.role === "agency",
  });
  const deviceQuery = useQuery({
    queryKey: ["devices"],
    queryFn: () => api<Device[]>("/network/devices"),
    enabled: enabled && me?.role === "agency",
  });
  const mutation = useMutation({
    mutationFn: ({
      path,
      data,
      method = "POST",
    }: {
      path: string;
      data: unknown;
      method?: string;
    }) => (method === "PATCH" ? patch(path, data) : post(path, data)),
    onSuccess: async () => {
      setSelected(null);
      await cache.invalidateQueries();
      setNotice("Changes saved.");
    },
  });
  if (!signedIn()) return <Navigate to="/login" replace />;
  if (accountError)
    return (
      <div className="loading-page">
        <ErrorNotice error={accountError} />
        <button
          className="button"
          onClick={async () => {
            await logout();
            cache.clear();
            navigate("/login");
          }}
        >
          Return to sign in
        </button>
      </div>
    );
  if (!me || !catalog)
    return (
      <div className="loading-page">
        <Brand />
        <p>Opening your workspace…</p>
      </div>
    );
  const role = me.role;
  const name = me.profile?.name || "there";
  const visits = visitsQuery.data || [];
  const jobs = jobsQuery.data || [];
  const team = teamQuery.data || [];
  const devices = deviceQuery.data || [];
  const section = location.pathname.split("/")[2] || "overview";
  const pending = visits.filter((v) => v.status === "requested");
  const upcoming = visits.filter((v) =>
    ["open", "accepted", "in_progress"].includes(v.status),
  );
  const completed = visits.filter((v) => v.status === "completed");
  const nav = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    {
      id: role === "provider" ? "discover" : "visits",
      label: role === "provider" ? "Find visits" : "Care visits",
      icon: role === "provider" ? Globe2 : CalendarDays,
    },
    { id: "schedule", label: "Schedule", icon: Clock3 },
    ...(role === "agency"
      ? [
          { id: "team", label: "Your people", icon: Users },
          { id: "devices", label: "Equipment", icon: Package },
        ]
      : []),
  ];
  const titles: Record<string, string> = {
    overview: `A little clarity, ${name.split(" ")[0]}.`,
    discover: "Good care. New connections.",
    visits: "Every visit, in view.",
    schedule: "Make room for care.",
    team: "The people behind the care.",
    devices: "Ready for the next visit.",
  };
  const source =
    section === "discover"
      ? jobs
      : section === "schedule"
        ? visits.filter((v) => ["accepted", "in_progress"].includes(v.status))
        : visits;
  const shown = source.filter(
    (v) =>
      (filter === "all" || v.status === filter) &&
      `${v.city} ${catalog?.services[v.service]} ${v.recipient || ""}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  const change = (v: Visit, action: string) =>
    mutation.mutate({
      path: `/network/visits/${v.id}/transition`,
      data: { action },
    });
  function rows(items: Visit[]) {
    return (
      <div className="visit-list">
        {items.map((v, i) => (
          <motion.button
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.035, 0.2) }}
            className="visit-row"
            key={v.id}
            onClick={() => {
              mutation.reset();
              setSelected(v);
            }}
          >
            <span className="visit-date">
              <strong>
                {new Intl.DateTimeFormat("en", {
                  day: "2-digit",
                  timeZone: v.timezone,
                }).format(new Date(v.starts_at))}
              </strong>
              <small>
                {new Intl.DateTimeFormat("en", {
                  month: "short",
                  timeZone: v.timezone,
                }).format(new Date(v.starts_at))}
              </small>
            </span>
            <span className="visit-main">
              <strong>{catalog?.services[v.service]}</strong>
              <small>
                {v.recipient || "Home visit"} · {v.city}
              </small>
            </span>
            <span className="visit-time">
              {date(v)}
              <small>{v.duration_minutes} minutes</small>
            </span>
            <Status value={v.status} />
            <ArrowUpRight size={18} />
          </motion.button>
        ))}
      </div>
    );
  }
  return (
    <div className="workspace">
      <aside className={"sidebar " + (mobile ? "mobile-open" : "")}>
        <LinkBrand />
        <button
          className="mobile-close icon-button"
          aria-label="Close menu"
          onClick={() => setMobile(false)}
        >
          <X />
        </button>
        <div className="workspace-label">
          <span className="workspace-avatar">{name.slice(0, 1)}</span>
          <div>
            <strong>
              {role === "agency"
                ? "Agency workspace"
                : role === "provider"
                  ? "Provider workspace"
                  : "Your care space"}
            </strong>
            <small>CareReady network</small>
          </div>
          <span className="live-dot" />
        </div>
        <p className="nav-caption">WORKSPACE</p>
        <nav>
          {nav.map((n) => (
            <NavLink
              key={n.id}
              to={"/app/" + n.id}
              onClick={() => {
                setMobile(false);
                setSearch("");
                setFilter("all");
              }}
              className={({ isActive }) =>
                isActive || (section === "overview" && n.id === "overview")
                  ? "nav-item active"
                  : "nav-item"
              }
            >
              <n.icon size={18} />
              {n.label}
              {n.id === "discover" && jobs.length > 0 && (
                <span className="nav-count">{jobs.length}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="small-note">
            <CircleHelp size={17} />
            <p>
              Thoughtful care starts
              <br />
              with a clear next step.
            </p>
          </div>
          <div className="account-row">
            <span className="avatar">
              {name
                .split(" ")
                .map((x) => x[0])
                .slice(0, 2)
                .join("")}
            </span>
            <div>
              <strong>{name}</strong>
              <small>{role}</small>
            </div>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={async () => {
                await logout();
                cache.clear();
                navigate("/login");
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <div>
            <button
              className="menu-button icon-button"
              onClick={() => setMobile(true)}
              aria-label="Open navigation"
            >
              <Menu />
            </button>
            <span>Workspace</span>
            <span className="slash">/</span>
            <strong>
              {nav.find((n) => n.id === section)?.label || "Overview"}
            </strong>
          </div>
          <span className="preview-pill">
            <i />
            Local preview
          </span>
        </header>
        <div className="page-content">
          <PageTitle
            eyebrow={
              role === "agency"
                ? "PEOPLE FIRST. ALWAYS."
                : role === "provider"
                  ? "YOUR NEXT CHAPTER IN CARE"
                  : "SUPPORT THAT FEELS PERSONAL"
            }
            title={titles[section] || titles.overview}
          >
            {role === "requester" && me.is_verified && (
              <Primary onClick={() => setNewRequest(true)}>
                <Plus size={17} />
                Request a visit
              </Primary>
            )}
          </PageTitle>
          {!me.is_verified ? (
            <div className="verification-card">
              <Mail size={32} />
              <h2>Let’s verify your email.</h2>
              <p>
                Check the local mailbox for {me.email}. Verify your address to
                open your workspace.
              </p>
              <div className="button-row">
                <a
                  className="button primary"
                  href="http://127.0.0.1:8029"
                  target="_blank"
                  rel="noreferrer"
                >
                  Open mailbox <ArrowUpRight size={16} />
                </a>
                <button
                  className="button"
                  onClick={() =>
                    mutation.mutate({
                      path: "/auth/verification-request",
                      data: { email: me.email },
                    })
                  }
                >
                  Resend email
                </button>
                <button
                  className="button"
                  onClick={() =>
                    cache.invalidateQueries({ queryKey: ["account"] })
                  }
                >
                  I’ve verified
                </button>
              </div>
              <ErrorNotice error={mutation.error} />
              {mutation.isSuccess && (
                <p role="status">
                  If eligible, a verification email has been queued.
                </p>
              )}
            </div>
          ) : (
            <>
              {notice && (
                <div className="toast" role="status">
                  <Check size={16} />
                  {notice}
                  <button
                    aria-label="Dismiss notification"
                    onClick={() => setNotice("")}
                  >
                    <X size={14} />
                  </button>
                </div>
              )}
              <ErrorNotice
                error={
                  visitsQuery.error ||
                  jobsQuery.error ||
                  teamQuery.error ||
                  deviceQuery.error ||
                  mutation.error
                }
              />
              {role === "provider" && !me.profile?.approved && (
                <div className="notice">
                  Your agency is reviewing your provider profile. Eligible
                  visits will appear here after approval.
                </div>
              )}
              {section === "overview" && (
                <>
                  <div className="overview-hero">
                    <div>
                      <span className="eyebrow">
                        {role === "agency"
                          ? "A CONNECTED CARE NETWORK"
                          : "A GOOD DAY BEGINS WITH SUPPORT"}
                      </span>
                      <h2>
                        {role === "agency"
                          ? "More time for people.\nLess time chasing plans."
                          : role === "provider"
                            ? "Your experience.\nSomeone’s better day."
                            : "Care that fits\ninto real life."}
                      </h2>
                      <p>
                        {role === "agency"
                          ? "Review requests, bring the right people together and keep every visit moving."
                          : role === "provider"
                            ? "Find visits suited to your experience, services and schedule."
                            : "One visit or a familiar weekly face. Arrange support, your way."}
                      </p>
                      <button
                        className="text-button"
                        onClick={() =>
                          navigate(
                            "/app/" +
                              (role === "provider" ? "discover" : "visits"),
                          )
                        }
                      >
                        {role === "provider"
                          ? "Explore available visits"
                          : "View care visits"}
                        <ArrowUpRight size={17} />
                      </button>
                    </div>
                    <div className="hero-emblem" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                      <span />
                      <i>
                        care
                        <br />
                        connects.
                      </i>
                    </div>
                    <span className="hero-edition">01 / THE CARE NETWORK</span>
                  </div>
                  <div className="stats-grid">
                    {[
                      {
                        label:
                          role === "provider"
                            ? "Available to you"
                            : "Awaiting review",
                        value:
                          role === "provider" ? jobs.length : pending.length,
                        note:
                          role === "provider"
                            ? "Matched to your profile"
                            : "Requests ready for a next step",
                      },
                      {
                        label: "Upcoming visits",
                        value: upcoming.length,
                        note: "Care on the calendar",
                      },
                      {
                        label: "Completed visits",
                        value: completed.length,
                        note: "Time well spent",
                      },
                    ].map((s, i) => (
                      <div className="stat" key={s.label}>
                        <span>{s.label}</span>
                        <div>
                          <Counter value={s.value} />
                          <span className="stat-index">0{i + 1}</span>
                        </div>
                        <small>{s.note}</small>
                      </div>
                    ))}
                  </div>
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">THE NEXT FEW STEPS</p>
                      <h2>
                        {role === "agency"
                          ? "Requests to review"
                          : "Your next visits"}
                      </h2>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => navigate("/app/visits")}
                    >
                      View all <ArrowRight size={15} />
                    </button>
                  </div>
                  {visitsQuery.isPending ? (
                    <p className="loading-line">Loading visits…</p>
                  ) : (role === "agency" ? pending : upcoming).length ? (
                    rows((role === "agency" ? pending : upcoming).slice(0, 4))
                  ) : (
                    <Empty title="A little breathing room">
                      {role === "requester"
                        ? "Your upcoming care will appear here. Start with a request whenever you’re ready."
                        : "New visits will appear here as your network gets moving."}
                    </Empty>
                  )}
                </>
              )}
              {["visits", "schedule", "discover"].includes(section) && (
                <>
                  {section === "discover" && (
                    <div className="map-panel">
                      <div className="map-copy">
                        <p className="eyebrow">YOUR WORLD OF CARE</p>
                        <h2>
                          Meaningful work.
                          <br />
                          <em>Closer than you think.</em>
                        </h2>
                        <p>
                          Explore available visits across your agency’s network.
                          Every point is a city, never someone’s home.
                        </p>
                        <div className="map-total">
                          <Counter value={jobs.length} />
                          <span>
                            eligible visits
                            <br />
                            in your network
                          </span>
                        </div>
                        <div className="map-key">
                          <i />
                          Available care visits
                        </div>
                      </div>
                      <Suspense
                        fallback={
                          <div className="map-fallback">
                            Preparing your globe…
                          </div>
                        }
                      >
                        <Globe jobs={jobs} onSelect={setSelected} />
                      </Suspense>
                    </div>
                  )}
                  <div className="list-toolbar">
                    <div className="search-field">
                      <Search size={17} />
                      <input
                        aria-label="Search visits"
                        placeholder="Search city or service"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                      />
                    </div>
                    {section !== "discover" && (
                      <select
                        aria-label="Filter visit status"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                      >
                        <option value="all">All statuses</option>
                        {[
                          "requested",
                          "open",
                          "accepted",
                          "in_progress",
                          "completed",
                          "cancelled",
                        ].map((s) => (
                          <option key={s} value={s}>
                            {friendly(s)}
                          </option>
                        ))}
                      </select>
                    )}
                    <span className="result-count">
                      {shown.length} {shown.length === 1 ? "visit" : "visits"}
                    </span>
                  </div>
                  {(section === "discover" ? jobsQuery : visitsQuery)
                    .isPending ? (
                    <p className="loading-line">Finding your visits…</p>
                  ) : shown.length ? (
                    rows(shown)
                  ) : (
                    <Empty
                      title={
                        section === "discover"
                          ? "No matching visits just yet"
                          : "Nothing here yet"
                      }
                    >
                      {section === "discover"
                        ? "New offers appear after your agency publishes a visit that fits your approved profile and schedule."
                        : "Try another filter or start with a new care request."}
                    </Empty>
                  )}
                </>
              )}
              {section === "team" && role === "agency" && (
                <>
                  <p className="section-description">
                    Review experience and services before approving a provider.
                    Email verification alone does not verify professional
                    qualifications.
                  </p>
                  <div className="team-grid">
                    {team.map((p) => (
                      <article className="person-card" key={p.user_id}>
                        <div className="person-top">
                          <span className="person-avatar">
                            {p.name
                              .split(" ")
                              .map((n) => n[0])
                              .slice(0, 2)
                              .join("")}
                          </span>
                          <Status value={p.approved ? "approved" : "pending"} />
                        </div>
                        <h3>{p.name}</h3>
                        <p className="muted">{p.email}</p>
                        <div className="person-meta">
                          <span>{catalog.experience_levels[p.experience]}</span>
                          <span>{p.languages.join(", ")}</span>
                        </div>
                        <div className="chips">
                          {p.services.map((s) => (
                            <span key={s}>{catalog.services[s]}</span>
                          ))}
                        </div>
                        <button
                          className={"button " + (p.approved ? "" : "primary")}
                          disabled={mutation.isPending || !p.is_verified}
                          onClick={() =>
                            mutation.mutate({
                              path: "/network/team/" + p.user_id,
                              method: "PATCH",
                              data: { approved: !p.approved },
                            })
                          }
                        >
                          {!p.is_verified
                            ? "Awaiting email verification"
                            : p.approved
                              ? "Pause approval"
                              : "Approve provider"}
                          <ArrowUpRight size={15} />
                        </button>
                      </article>
                    ))}
                  </div>
                  {team.length === 0 && (
                    <Empty title="Good people make the difference">
                      Providers can select your verified agency when they sign
                      up. Their profiles will appear here for review.
                    </Empty>
                  )}
                </>
              )}
              {section === "devices" && role === "agency" && (
                <Equipment
                  devices={devices}
                  busy={mutation.isPending}
                  change={(id, status) =>
                    mutation.mutate({
                      path: "/network/devices/" + id,
                      method: "PATCH",
                      data: { status },
                    })
                  }
                />
              )}
            </>
          )}
          <footer className="page-footer">
            <span>CareReady · Thoughtfully connected.</span>
            <span>Local demonstration · Fictional information only</span>
          </footer>
        </div>
      </main>
      {newRequest && (
        <Modal
          title="Arrange a little support"
          onClose={() => setNewRequest(false)}
        >
          <RequestForm
            catalog={catalog}
            onDone={() => {
              setNewRequest(false);
              setNotice("Your request is with the agency.");
            }}
          />
        </Modal>
      )}
      {selected && (
        <Modal
          title={catalog.services[selected.service]}
          onClose={() => setSelected(null)}
        >
          <div className="detail-body">
            <div className="detail-intro">
              <Status value={selected.status} />
              <span>
                <MapPin size={15} />
                {selected.city}
              </span>
            </div>
            <h3>{date(selected)}</h3>
            <p className="muted">
              {selected.duration_minutes} minutes ·{" "}
              {catalog.experience_levels[selected.min_experience]} minimum
              experience
            </p>
            {selected.recipient && (
              <div className="private-details">
                <strong>{selected.recipient}</strong>
                <p>{selected.address}</p>
              </div>
            )}
            <div className="detail-grid">
              <div>
                <small>Preferred language</small>
                <strong>
                  {selected.preferred_language === "any"
                    ? "No preference"
                    : selected.preferred_language}
                </strong>
              </div>
              <div>
                <small>Gender preference</small>
                <strong>
                  {selected.gender_preference === "any"
                    ? "No preference"
                    : friendly(selected.gender_preference)}
                </strong>
              </div>
              <div>
                <small>Communication</small>
                <strong>{friendly(selected.communication)}</strong>
              </div>
              <div>
                <small>At home</small>
                <strong>
                  {selected.pets_present ? "Pets present" : "No pets noted"}
                  {selected.smoke_free ? " · Smoke-free requested" : ""}
                </strong>
              </div>
            </div>
            {selected.notes && (
              <div className="detail-note">
                <small>Visit notes</small>
                <p>{selected.notes}</p>
              </div>
            )}
            {!selected.address && (
              <p className="hint">
                The exact address and recipient details become available after
                you accept. Preferences help assess fit; they are not guaranteed
                matches.
              </p>
            )}
            <ErrorNotice error={mutation.error} />
            <div className="button-row">
              {role === "provider" && selected.status === "open" && (
                <button
                  className="button primary"
                  disabled={mutation.isPending}
                  onClick={() =>
                    mutation.mutate({
                      path: "/network/jobs/" + selected.id + "/accept",
                      data: {},
                    })
                  }
                >
                  Accept visit <Check size={16} />
                </button>
              )}
              {role === "agency" && selected.status === "requested" && (
                <button
                  className="button primary"
                  disabled={mutation.isPending}
                  onClick={() => change(selected, "publish")}
                >
                  Publish to eligible providers <ArrowUpRight size={15} />
                </button>
              )}
              {role === "provider" &&
                ["accepted", "in_progress"].includes(selected.status) && (
                  <button
                    className="button primary"
                    disabled={mutation.isPending}
                    onClick={() =>
                      change(
                        selected,
                        selected.status === "accepted" ? "start" : "complete",
                      )
                    }
                  >
                    {selected.status === "accepted"
                      ? "Start visit"
                      : "Complete visit"}
                  </button>
                )}
              {["requester", "agency"].includes(role) &&
                ["requested", "open", "accepted"].includes(selected.status) && (
                  <button
                    className="button danger"
                    disabled={mutation.isPending}
                    onClick={() => {
                      if (
                        window.confirm(
                          "Cancel this visit only? Other recurring visits will remain scheduled.",
                        )
                      )
                        change(selected, "cancel");
                    }}
                  >
                    Cancel this visit
                  </button>
                )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
function LinkBrand() {
  return (
    <NavLink to="/app/overview" aria-label="CareReady overview">
      <Brand />
    </NavLink>
  );
}
function Equipment({
  devices,
  busy,
  change,
}: {
  devices: Device[];
  busy: boolean;
  change: (id: string, status: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const cache = useQueryClient();
  const add = useMutation({
    mutationFn: (data: unknown) => post("/network/devices", data),
    onSuccess: () => {
      setOpen(false);
      cache.invalidateQueries({ queryKey: ["devices"] });
    },
  });
  return (
    <>
      <div className="section-heading">
        <p className="section-description">
          A simple inventory for your agency. Track condition and availability;
          visit reservations are not yet automated.
        </p>
        <Primary onClick={() => setOpen(true)}>
          <Plus size={16} />
          Add equipment
        </Primary>
      </div>
      {devices.length ? (
        <div className="equipment-list">
          {devices.map((d) => (
            <div className="equipment-row" key={d.id}>
              <span className="equipment-icon">
                <Package size={23} />
              </span>
              <div>
                <h3>{d.name}</h3>
                <small>{d.asset_code}</small>
              </div>
              <Status value={d.status} />
              <select
                aria-label={"Status for " + d.name}
                value={d.status}
                disabled={busy}
                onChange={(e) => change(d.id, e.target.value)}
              >
                <option value="available">Available</option>
                <option value="in_use">In use</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
          ))}
        </div>
      ) : (
        <Empty title="A place for every essential">
          Add your agency’s equipment and keep its availability visible.
        </Empty>
      )}
      {open && (
        <Modal title="Add equipment" onClose={() => setOpen(false)}>
          <form
            className="detail-body"
            onSubmit={(e) => {
              e.preventDefault();
              const d = new FormData(e.currentTarget);
              add.mutate({
                name: d.get("name"),
                asset_code: d.get("asset_code"),
                status: "available",
              });
            }}
          >
            <label>
              Equipment name
              <input
                name="name"
                required
                minLength={2}
                maxLength={100}
                placeholder="Portable blood pressure monitor"
              />
            </label>
            <label>
              Asset code
              <input
                name="asset_code"
                required
                minLength={2}
                maxLength={40}
                placeholder="CR-001"
              />
            </label>
            <ErrorNotice error={add.error} />
            <button className="button primary" disabled={add.isPending}>
              Add equipment <Plus size={17} />
            </button>
          </form>
        </Modal>
      )}
    </>
  );
}
