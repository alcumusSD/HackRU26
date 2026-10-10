"use client";

import { useEffect, useState } from "react";
import { fetchGenes, fetchJudgment, fetchTrials } from "@/lib/api";
import type { Gene, JudgmentCard, Trial } from "@/lib/types";
import { QUADRANT_META } from "@/lib/quadrant";
import { JudgmentPanel } from "./JudgmentPanel";
import { QuadrantMap } from "./QuadrantMap";

export function RadarApp() {
  const [genes, setGenes] = useState<Gene[]>([]);
  const [dataAsOf, setDataAsOf] = useState<string>("");
  const [cached, setCached] = useState(true);
  const [disease, setDisease] = useState("asthma");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [selected, setSelected] = useState<Gene | null>(null);
  const [judgment, setJudgment] = useState<JudgmentCard | null>(null);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [protectiveOnly, setProtectiveOnly] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setLoadError(null);
    fetchGenes("asthma")
      .then((res) => {
        if (cancelled) return;
        setGenes(res.genes);
        setDataAsOf(res.data_as_of);
        setCached(res.cached);
        setDisease(res.disease);
      })
      .catch((err: Error) => {
        if (!cancelled) setLoadError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function selectGene(gene: Gene) {
    setSelected(gene);
    setDetailLoading(true);
    setDetailError(null);
    setJudgment(null);
    setTrials([]);
    try {
      const [j, t] = await Promise.all([
        fetchJudgment(gene.id),
        fetchTrials(gene.id),
      ]);
      setJudgment(j);
      setTrials(t);
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className={`radar-stage ${selected ? "has-panel" : ""}`}>
      <div className="radar-atmosphere" aria-hidden />
      <div className="radar-sweep" aria-hidden />

      <header className="radar-header">
        <div>
          <p className="brand-mark">Evidence Radar</p>
          <h1>
            One live map for {disease}
            <span className="h1-sub">
              Genetic evidence versus trial activity — with proof beside every
              score.
            </span>
          </h1>
        </div>
        <div className="header-meta">
          <label className="toggle">
            <input
              type="checkbox"
              checked={protectiveOnly}
              onChange={(e) => setProtectiveOnly(e.target.checked)}
            />
            Protective-variant genes only
          </label>
          <p className="status-pill">
            {cached ? "Using cached data" : "Live data"} · as of{" "}
            {dataAsOf || "—"}
          </p>
        </div>
      </header>

      <main className="radar-main">
        <section className="map-pane" aria-label="Evidence versus activity map">
          {loading && <p className="map-state">Loading map…</p>}
          {loadError && (
            <p className="map-state error">
              Could not reach the API. Start the backend on port 8000.
              <br />
              <small>{loadError}</small>
            </p>
          )}
          {!loading && !loadError && (
            <QuadrantMap
              genes={genes}
              selectedId={selected?.id ?? null}
              onSelect={selectGene}
              protectiveOnly={protectiveOnly}
            />
          )}
        </section>

        <JudgmentPanel
          gene={selected}
          judgment={judgment}
          trials={trials}
          loading={detailLoading}
          error={detailError}
          onClose={() => setSelected(null)}
        />
      </main>

      <footer className="radar-footer">
        <div className="legend">
          {(Object.keys(QUADRANT_META) as Array<keyof typeof QUADRANT_META>).map(
            (key) => (
              <span key={key} className={`legend-item legend-${key}`}>
                {QUADRANT_META[key].label}
              </span>
            ),
          )}
        </div>
        <p>
          Data sources: Open Targets, ClinicalTrials.gov, GWAS Catalog (mock
          path). Evidence strength, not a recommendation.
        </p>
      </footer>
    </div>
  );
}
