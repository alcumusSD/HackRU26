"use client";

import { useMemo, type KeyboardEvent, type MouseEvent } from "react";
import {
  CartesianGrid,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { Gene, Quadrant } from "@/lib/types";
import { QUADRANT_CUTOFF, QUADRANT_META } from "@/lib/quadrant";

type Props = {
  genes: Gene[];
  selectedId: string | null;
  onSelect: (gene: Gene) => void;
  protectiveOnly: boolean;
};

const FILL: Record<Quadrant, string> = {
  validated: "#0f766e",
  white_space: "#b45309",
  caution: "#a16207",
  deprioritize: "#64748b",
};

function GeneShape(props: {
  cx?: number;
  cy?: number;
  payload?: Gene;
  selectedId: string | null;
  onSelect: (gene: Gene) => void;
}) {
  const { cx = 0, cy = 0, payload, selectedId, onSelect } = props;
  if (!payload) return null;

  const selected = payload.id === selectedId;
  const size = selected ? 11 : payload.protective_variant ? 9 : 7;
  const fill = FILL[payload.quadrant];
  const stroke = selected ? "#0c1f24" : "#f4f7f6";
  const strokeWidth = selected ? 2.5 : 1.25;
  const shape = QUADRANT_META[payload.quadrant].shape;
  const handlers = {
    onClick: (e: MouseEvent) => {
      e.stopPropagation();
      onSelect(payload);
    },
    style: { cursor: "pointer" as const },
    role: "button" as const,
    tabIndex: 0,
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect(payload);
      }
    },
  };

  if (shape === "diamond") {
    const d = size + 1;
    return (
      <polygon
        points={`${cx},${cy - d} ${cx + d},${cy} ${cx},${cy + d} ${cx - d},${cy}`}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        className={selected ? "gene-pulse" : undefined}
        {...handlers}
      />
    );
  }
  if (shape === "square") {
    return (
      <rect
        x={cx - size}
        y={cy - size}
        width={size * 2}
        height={size * 2}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        className={selected ? "gene-pulse" : undefined}
        {...handlers}
      />
    );
  }
  if (shape === "triangle") {
    const d = size + 2;
    return (
      <polygon
        points={`${cx},${cy - d} ${cx + d},${cy + d * 0.7} ${cx - d},${cy + d * 0.7}`}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth}
        className={selected ? "gene-pulse" : undefined}
        {...handlers}
      />
    );
  }
  return (
    <circle
      cx={cx}
      cy={cy}
      r={size}
      fill={fill}
      stroke={stroke}
      strokeWidth={strokeWidth}
      className={selected ? "gene-pulse" : undefined}
      {...handlers}
    />
  );
}

function MapTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: Gene }[];
}) {
  if (!active || !payload?.[0]) return null;
  const g = payload[0].payload;
  const meta = QUADRANT_META[g.quadrant];
  return (
    <div className="map-tooltip">
      <strong>{g.symbol}</strong>
      <span>{meta.label}</span>
      <span>
        Evidence {g.genetic_score.toFixed(2)} · Activity{" "}
        {g.activity_score.toFixed(2)}
      </span>
    </div>
  );
}

export function QuadrantMap({
  genes,
  selectedId,
  onSelect,
  protectiveOnly,
}: Props) {
  const data = useMemo(
    () =>
      genes.filter((g) => (protectiveOnly ? g.protective_variant : true)),
    [genes, protectiveOnly],
  );

  return (
    <div className="map-shell">
      <div className="map-quadrant-labels" aria-hidden>
        <span className="ql ql-nw">
          <em>White space</em>
          Strong genetics, few trials
        </span>
        <span className="ql ql-ne">
          <em>Validated</em>
          Strong genetics, active programs
        </span>
        <span className="ql ql-sw">
          <em>Deprioritize</em>
          Thin genetics, little activity
        </span>
        <span className="ql ql-se">
          <em>Caution</em>
          Busy clinically, thinner genetics
        </span>
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 28, right: 28, bottom: 36, left: 16 }}>
          <CartesianGrid stroke="rgba(12, 31, 36, 0.08)" strokeDasharray="3 6" />
          <ReferenceArea
            x1={0}
            x2={QUADRANT_CUTOFF}
            y1={QUADRANT_CUTOFF}
            y2={1}
            fill="rgba(180, 83, 9, 0.06)"
          />
          <ReferenceArea
            x1={QUADRANT_CUTOFF}
            x2={1}
            y1={QUADRANT_CUTOFF}
            y2={1}
            fill="rgba(15, 118, 110, 0.07)"
          />
          <ReferenceArea
            x1={0}
            x2={QUADRANT_CUTOFF}
            y1={0}
            y2={QUADRANT_CUTOFF}
            fill="rgba(100, 116, 139, 0.05)"
          />
          <ReferenceArea
            x1={QUADRANT_CUTOFF}
            x2={1}
            y1={0}
            y2={QUADRANT_CUTOFF}
            fill="rgba(161, 98, 7, 0.06)"
          />
          <XAxis
            type="number"
            dataKey="activity_score"
            name="Trial activity"
            domain={[0, 1]}
            tickCount={5}
            tick={{ fill: "#3d565c", fontSize: 12 }}
            axisLine={{ stroke: "#9bb0b4" }}
            label={{
              value: "Trial activity →",
              position: "insideBottom",
              offset: -18,
              fill: "#3d565c",
              fontSize: 13,
            }}
          />
          <YAxis
            type="number"
            dataKey="genetic_score"
            name="Genetic evidence"
            domain={[0, 1]}
            tickCount={5}
            tick={{ fill: "#3d565c", fontSize: 12 }}
            axisLine={{ stroke: "#9bb0b4" }}
            label={{
              value: "Genetic evidence →",
              angle: -90,
              position: "insideLeft",
              offset: 10,
              fill: "#3d565c",
              fontSize: 13,
            }}
          />
          <ZAxis range={[80, 80]} />
          <ReferenceLine
            x={QUADRANT_CUTOFF}
            stroke="rgba(12, 31, 36, 0.28)"
            strokeDasharray="5 5"
          />
          <ReferenceLine
            y={QUADRANT_CUTOFF}
            stroke="rgba(12, 31, 36, 0.28)"
            strokeDasharray="5 5"
          />
          <Tooltip
            content={<MapTooltip />}
            cursor={{ strokeDasharray: "3 3", stroke: "#0f766e" }}
          />
          <Scatter
            data={data}
            isAnimationActive
            animationDuration={700}
            shape={(props: {
              cx?: number;
              cy?: number;
              payload?: Gene;
            }) => (
              <GeneShape
                cx={props.cx}
                cy={props.cy}
                payload={props.payload}
                selectedId={selectedId}
                onSelect={onSelect}
              />
            )}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
