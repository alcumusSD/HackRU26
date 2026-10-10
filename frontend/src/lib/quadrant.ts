import type { Quadrant } from "./types";

export const QUADRANT_CUTOFF = 0.5;

export const QUADRANT_META: Record<
  Quadrant,
  { label: string; plain: string; shape: "circle" | "diamond" | "square" | "triangle" }
> = {
  validated: {
    label: "Validated",
    plain: "Strong genetics, active clinical testing",
    shape: "circle",
  },
  white_space: {
    label: "White space",
    plain: "Strong genetics, little clinical testing",
    shape: "diamond",
  },
  caution: {
    label: "Caution",
    plain: "Busy clinically, thinner genetic support",
    shape: "square",
  },
  deprioritize: {
    label: "Deprioritize",
    plain: "Thin genetics and limited activity",
    shape: "triangle",
  },
};

export function formatMissing(code: string): string {
  return code.replace(/_/g, " ");
}
