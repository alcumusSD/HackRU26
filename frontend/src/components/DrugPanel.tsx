"use client";

import type { Gene } from "@/lib/types";

export type SelectedDrug = {
  id: string;
  name: string;
  degree: number;
  trial_count: number;
  connectedGenes: Gene[];
};

type Props = {
  drug: SelectedDrug;
  onClose: () => void;
  onSelectGene: (gene: Gene) => void;
};

export function DrugPanel({ drug, onClose, onSelectGene }: Props) {
  return (
    <aside className="judgment-panel drug-panel" aria-label={`Drug ${drug.name}`}>
      <div className="judgment-panel__head">
        <div>
          <p className="eyebrow">Selected drug</p>
          <h2>{drug.name}</h2>
          <p className="plain">
            Linked to {drug.degree} gene{drug.degree === 1 ? "" : "s"} in this
            network · {drug.trial_count} trial mentions
          </p>
        </div>
        <button type="button" className="close-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <p className="disclaimer">
        Clinical neighborhood from trial interventions — not a recommendation.
      </p>

      <section>
        <h3>Connected genes</h3>
        {drug.connectedGenes.length === 0 ? (
          <p className="muted">No linked genes in the current filter.</p>
        ) : (
          <ul className="drug-gene-list">
            {drug.connectedGenes.map((gene) => (
              <li key={gene.id}>
                <button type="button" onClick={() => onSelectGene(gene)}>
                  <strong>{gene.symbol}</strong>
                  <span>
                    evidence {gene.genetic_score.toFixed(2)} · activity{" "}
                    {gene.activity_score.toFixed(2)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </aside>
  );
}
