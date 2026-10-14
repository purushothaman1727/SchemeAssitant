import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { I18nProvider } from "../i18n";
import type { RecommendationCard, RecommendationResponse } from "../types/api";
import Results from "./Results";

vi.mock("../services/api", () => ({
  getRecommendations: vi.fn(),
  errorMessage: () => "Cannot reach the server. Check your connection and try again.",
}));
import { getRecommendations } from "../services/api";

const card = (over: Partial<RecommendationCard>): RecommendationCard => ({
  scheme_id: "x", name: "Scheme X", name_ta: null, jurisdiction: "central", jurisdiction_label: "Central Government",
  category: "scholarship", status: "potentially_eligible", why_relevant: ["Because reasons"], reasons: ["Meets: criteria"],
  missing_fields: [], benefits: null, required_documents: [], application_steps: [], official_url: "https://depwd.gov.in/x",
  application_url: null, last_verified: "2026-10-13", verification_status: "verified", accepting_applications: null,
  limitations: ["Open/closed status unknown"], score: 80, show_by_default: true, ...over,
});

const response = (results: RecommendationCard[]): RecommendationResponse => ({
  results, counts: {}, disclaimer: "Preliminary guidance only.",
});

function renderPage() {
  return render(
    <I18nProvider><MemoryRouter><Results /></MemoryRouter></I18nProvider>,
  );
}

beforeEach(() => {
  sessionStorage.setItem("profile.v1", JSON.stringify({ age: 14 }));
  vi.mocked(getRecommendations).mockReset();
});

describe("Results page", () => {
  it("asks the user to fill the form when there is no profile", () => {
    sessionStorage.clear();
    renderPage();
    expect(screen.getByText(/answer the questions first/i)).toBeInTheDocument();
  });

  it("shows cards with status text, official link and last-verified date", async () => {
    vi.mocked(getRecommendations).mockResolvedValue(response([card({})]));
    renderPage();
    expect(await screen.findByText("Scheme X")).toBeInTheDocument();
    expect(screen.getByText("Potentially eligible")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /official source/i })).toHaveAttribute("href", "https://depwd.gov.in/x");
    expect(screen.getByText(/2026-10-13/)).toBeInTheDocument();
    expect(screen.getByText("Preliminary guidance only.")).toBeInTheDocument();
  });

  it("hides non-matching schemes until the user asks", async () => {
    vi.mocked(getRecommendations).mockResolvedValue(response([
      card({ scheme_id: "a", name: "Visible one" }),
      card({ scheme_id: "b", name: "Hidden one", status: "does_not_match", show_by_default: false }),
    ]));
    renderPage();
    await screen.findByText("Visible one");
    expect(screen.queryByText("Hidden one")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /show schemes that do not match/i }));
    expect(screen.getByText("Hidden one")).toBeInTheDocument();
  });

  it("shows an empty state when nothing is shown by default", async () => {
    vi.mocked(getRecommendations).mockResolvedValue(response([
      card({ status: "does_not_match", show_by_default: false }),
    ]));
    renderPage();
    expect(await screen.findByText(/no schemes matched/i)).toBeInTheDocument();
  });

  it("shows a retryable error and recovers", async () => {
    vi.mocked(getRecommendations).mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce(response([card({ name: "Recovered scheme" })]));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(/cannot reach the server/i);
    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    await waitFor(() => expect(screen.getByText("Recovered scheme")).toBeInTheDocument());
  });

  it("lists missing information in plain words", async () => {
    vi.mocked(getRecommendations).mockResolvedValue(response([
      card({ status: "more_information_required", missing_fields: ["disability_percentage"] }),
    ]));
    renderPage();
    expect(await screen.findByText("Disability percentage")).toBeInTheDocument();
    expect(screen.getByText("More information required")).toBeInTheDocument();
  });
});
