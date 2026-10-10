"use client";

import dynamic from "next/dynamic";
import type { Gene } from "@/lib/types";
import type { SelectedDrug } from "./DrugPanel";

const GeneSpace3D = dynamic(
  () => import("./GeneSpace3D").then((m) => m.GeneSpace3D),
  {
    ssr: false,
    loading: () => <p className="map-state">Loading network…</p>,
  },
);

type Props = {
  genes: Gene[];
  selectedId: string | null;
  onSelect: (gene: Gene) => void;
  onSelectDrug: (drug: SelectedDrug) => void;
  onClearDrug: () => void;
  protectiveOnly: boolean;
  disease?: string;
};

export function GeneSpace3DLazy(props: Props) {
  return <GeneSpace3D {...props} />;
}
