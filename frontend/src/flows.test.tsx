// @vitest-environment jsdom
import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { ReactNode } from "react";
import { api, post } from "./api";
import Auth from "./Auth";
import App from "./App";
import RequestForm from "./RequestForm";
import type { Catalog } from "./types";
vi.mock("./api", () => ({ api: vi.fn(), post: vi.fn(), setTokens: vi.fn() }));
const catalog: Catalog = {
  services: { companionship: "Companionship", nursing: "Nursing visit" },
  cities: {
    Toronto: {
      latitude: 43.65,
      longitude: -79.38,
      timezone: "America/Toronto",
    },
  },
  experience_levels: ["New to care", "1–2 years", "3–5 years", "6+ years"],
  languages: ["English", "French"],
};
function show(node: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{node}</MemoryRouter>
    </QueryClientProvider>,
  );
}
beforeEach(() => {
  vi.mocked(api).mockImplementation(async (path) =>
    path === "/network/catalog"
      ? catalog
      : ([{ id: "agency-1", name: "Demo agency", city: "Toronto" }] as never),
  );
  vi.mocked(post).mockResolvedValue({ verification_queued: true });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
describe("Role-specific onboarding", () => {
  it("asks providers for agency, services and languages without exposing an admin role", async () => {
    show(<Auth mode="signup" />);
    fireEvent.click(screen.getByRole("button", { name: "I provide care" }));
    expect(
      await screen.findByRole("option", { name: "Demo agency · Toronto" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Services you provide")).toBeInTheDocument();
    expect(screen.getByText("Languages you speak")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /admin/i }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "I need care" }));
    expect(screen.queryByText("Services you provide")).not.toBeInTheDocument();
  });
  it("shows a readable server failure and allows retry", async () => {
    vi.mocked(post).mockRejectedValueOnce(
      new Error("Invalid email or password"),
    );
    show(<Auth />);
    fireEvent.change(screen.getByLabelText("Email address"), {
      target: { value: "demo@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrong-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid email or password",
    );
    expect(screen.getByRole("button", { name: "Sign in" })).not.toBeDisabled();
  });
});
it("submits recurrence and preferences in the selected city timezone", async () => {
  const done = vi.fn();
  show(<RequestForm catalog={catalog} onDone={done} />);
  await screen.findByRole("option", { name: "Demo agency" });
  fireEvent.change(screen.getByLabelText("Who is receiving care?"), {
    target: { value: "Fictional person" },
  });
  fireEvent.change(screen.getByLabelText("Care agency"), {
    target: { value: "agency-1" },
  });
  fireEvent.change(screen.getByLabelText(/Visit address/), {
    target: { value: "Fictional address" },
  });
  fireEvent.change(screen.getByLabelText(/First visit/), {
    target: { value: "2026-11-02T10:00" },
  });
  fireEvent.change(screen.getByLabelText("Repeat"), { target: { value: "4" } });
  fireEvent.change(screen.getByLabelText("Preferred language"), {
    target: { value: "French" },
  });
  fireEvent.click(screen.getByLabelText("Pets in the home"));
  fireEvent.click(screen.getByLabelText(/I’m requesting for myself/));
  fireEvent.click(screen.getByRole("button", { name: "Send care request" }));
  await waitFor(() =>
    expect(post).toHaveBeenCalledWith(
      "/network/visits",
      expect.objectContaining({
        occurrences: 4,
        preferred_language: "French",
        pets_present: true,
        consent_confirmed: true,
        starts_at: "2026-11-02T15:00:00.000Z",
      }),
    ),
  );
  await waitFor(() => expect(done).toHaveBeenCalled());
});

it("returns from verification success to a fresh sign-in form", async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/verify/fictional-token"]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Verify email" }));
  const back = await screen.findByRole("link", { name: "Back to sign in" });
  fireEvent.click(back);
  expect(await screen.findByLabelText("Email address")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  expect(
    screen.queryByText("Your email is verified. You can now sign in."),
  ).not.toBeInTheDocument();
});
