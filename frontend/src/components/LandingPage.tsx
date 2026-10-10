"use client";

import { useState } from "react";

export type EnterIntent = "map" | "space3d";

type ExplainerTab = "map" | "network" | "judgment" | "ask";

type Props = {
  onEnter: (intent: EnterIntent) => void;
};

const TABS: {
  id: ExplainerTab;
  label: string;
  title: string;
  body: string;
  intent: EnterIntent;
  cta: string;
}[] = [
  {
    id: "map",
    label: "Map",
    title: "Evidence versus activity",
    body: "Each gene sits on a live quadrant: Open Targets genetic support on one axis, ClinicalTrials.gov activity on the other. Scores mean evidence strength — not success probability.",
    intent: "map",
    cta: "Enter Map",
  },
  {
    id: "network",
    label: "Network",
    title: "Gene–drug neighborhood",
    body: "A different view of the same cache: which interventions link to which targets, built from trial joins — clinical neighborhood, not the score scatter.",
    intent: "space3d",
    cta: "Open Network",
  },
  {
    id: "judgment",
    label: "Judgment",
    title: "For, Against, Missing",
    body: "Select a gene for a card assembled from scores and trials. Against items use ClinicalTrials.gov whyStopped text with quote verification. Try IL5 for terminated studies with receipts.",
    intent: "map",
    cta: "Open Map & pick a gene",
  },
  {
    id: "ask",
    label: "Ask",
    title: "Grounded assistant",
    body: "Chat answers only from what is on screen — selected gene, scores, trials, judgment. No open-web medical advice. Key stays on the backend.",
    intent: "map",
    cta: "Enter Map & ask",
  },
];

export function LandingPage({ onEnter }: Props) {
  const [tab, setTab] = useState<ExplainerTab>("map");
  const active = TABS.find((t) => t.id === tab) ?? TABS[0];

  return (
    <div className="landing">
      <div className="radar-atmosphere" aria-hidden />
      <div className="radar-sweep landing-sweep" aria-hidden />

      <div className="landing-inner">
        <section className="landing-hero" aria-label="Evidence Radar">
          <p className="brand-mark landing-brand">Evidence Radar</p>
          <h1 className="landing-headline">
            See which targets have genetic weight — and which trials actually moved.
          </h1>
          <p className="landing-support">
            Asthma demo: Open Targets + ClinicalTrials.gov, with a judgment layer
            and grounded chat beside the map.
          </p>
          <div className="landing-cta-group">
            <button
              type="button"
              className="landing-cta landing-cta--primary"
              onClick={() => onEnter("map")}
            >
              Enter Map
            </button>
            <button
              type="button"
              className="landing-cta landing-cta--secondary"
              onClick={() => onEnter("space3d")}
            >
              Open Network
            </button>
          </div>
        </section>

        <section className="landing-explore" aria-label="How to explore">
          <div className="landing-tabs view-tabs" role="tablist" aria-label="Product areas">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                className={tab === t.id ? "active" : ""}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div
            key={active.id}
            className="landing-panel"
            role="tabpanel"
            aria-label={active.label}
          >
            <h2>{active.title}</h2>
            <p>{active.body}</p>
            <button
              type="button"
              className="landing-cta landing-cta--ghost"
              onClick={() => onEnter(active.intent)}
            >
              {active.cta}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
