"use client";

import type { Gene, JudgmentCard, Trial } from "@/lib/types";
import { QUADRANT_META, formatMissing } from "@/lib/quadrant";

type Props = {
  gene: Gene | null;
  judgment: JudgmentCard | null;
  trials: Trial[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
};

export function JudgmentPanel({
  gene,
  judgment,
  trials,
  loading,
  error,
  onClose,
}: Props) {
  if (!gene) return null;

  const meta = QUADRANT_META[gene.quadrant];

  return (
    <aside className="judgment-panel" aria-label={`Judgment for ${gene.symbol}`}>
      <div className="judgment-panel__head">
        <div>
          <p className="eyebrow">Selected target</p>
          <h2>{gene.symbol}</h2>
          <p className="plain">{meta.plain}</p>
        </div>
        <button type="button" className="close-btn" onClick={onClose}>
          Close
        </button>
      </div>

      <p className="disclaimer">
        Evidence quality and open questions — not a recommendation.
      </p>

      <div className="score-row">
        <div>
          <span>Evidence</span>
          <strong>{gene.genetic_score.toFixed(2)}</strong>
        </div>
        <div>
          <span>Activity</span>
          <strong>{gene.activity_score.toFixed(2)}</strong>
        </div>
        <div>
          <span>Quadrant</span>
          <strong>{meta.label}</strong>
        </div>
      </div>

      {loading && <p className="muted">Loading judgment…</p>}
      {error && <p className="error">{error}</p>}

      {judgment && !loading && (
        <>
          <section>
            <h3>Robustness</h3>
            <p className="robustness">
              Top {judgment.robustness.top_k} in{" "}
              <strong>
                {Math.round(judgment.robustness.share_in_top_k * 100)}%
              </strong>{" "}
              of {judgment.robustness.runs.toLocaleString()} reweighted runs
              <span className={`tag tag-${judgment.robustness.label}`}>
                {judgment.robustness.label} — rank stability, not success
                probability
              </span>
            </p>
          </section>

          <section>
            <h3>For</h3>
            <ul>
              {judgment.for.map((item) => (
                <li key={item.text}>
                  <p>{item.text}</p>
                  <small>
                    {item.source} · {item.date}
                  </small>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h3>Against</h3>
            {judgment.against.length === 0 ? (
              <p className="muted">No terminated/withdrawn studies with stop text.</p>
            ) : (
              <ul>
                {judgment.against.map((item) => (
                  <li key={item.id}>
                    <p>{item.text}</p>
                    {item.quote && (
                      <blockquote className={item.quote_verified ? "quote-verified" : "quote-raw"}>
                        “{item.quote}”
                      </blockquote>
                    )}
                    <small>
                      {item.source}
                      {item.quote_verified
                        ? " · quote verified"
                        : item.quote
                          ? " · quote unverified"
                          : ""}
                    </small>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h3>Missing</h3>
            {judgment.missing.length === 0 ? (
              <p className="muted">No major gaps flagged.</p>
            ) : (
              <ul className="chips">
                {judgment.missing.map((m) => (
                  <li key={m}>{formatMissing(m)}</li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h3>Could change if</h3>
            <ul>
              {judgment.could_change_if.map((item) => (
                <li key={item.event}>
                  <p>
                    <strong>{formatMissing(item.event)}</strong> — {item.effect}
                  </p>
                </li>
              ))}
            </ul>
          </section>

          {judgment.conflicts.length > 0 && (
            <section>
              <h3>Conflicts</h3>
              <ul>
                {judgment.conflicts.map((c) => (
                  <li key={c.claim_a}>
                    <p>{c.claim_a}</p>
                    <p>{c.claim_b}</p>
                    <small>Difference: {c.difference}</small>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {judgment.open_questions.length > 0 && (
            <section>
              <h3>Open questions</h3>
              <ol>
                {judgment.open_questions.map((q) => (
                  <li key={q}>{q}</li>
                ))}
              </ol>
            </section>
          )}

          <p className="muted tiny">
            Card confidence: {judgment.card_confidence} · Data as of{" "}
            {judgment.data_as_of}
          </p>
        </>
      )}

      {trials.length > 0 && (
        <section>
          <h3>Linked trials</h3>
          <ul className="trials">
            {trials.map((t) => (
              <li key={t.nct_id}>
                <a
                  className="trial-link"
                  href={`https://clinicaltrials.gov/study/${t.nct_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t.nct_id}
                </a>{" "}
                · {t.phase} · {t.status}
                {t.stop_reason_category && (
                  <span>
                    {" "}
                    · stop: {t.stop_reason_category.replace(/_/g, " ")}
                    {t.quote_verified ? " ✓" : ""}
                  </span>
                )}
                {t.stop_reason_quote && (
                  <p className="trial-stop-quote">“{t.stop_reason_quote}”</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {gene.score_breakdown.length > 0 && (
        <section>
          <h3>Score breakdown</h3>
          <ul className="breakdown">
            {gene.score_breakdown.map((b) => (
              <li key={b.component}>
                <span>{b.component.replace(/_/g, " ")}</span>
                <span>
                  {b.value.toFixed(2)} × {b.weight.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  );
}
