"use client";

import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ForceGraph3D, { type ForceGraphMethods } from "react-force-graph-3d";
import SpriteText from "three-spritetext";
import { Group } from "three";
import { fetchNetwork } from "@/lib/api";
import type { Gene, NetworkLink, NetworkNode, Quadrant } from "@/lib/types";
import type { SelectedDrug } from "./DrugPanel";

type Props = {
  genes: Gene[];
  selectedId: string | null;
  onSelect: (gene: Gene) => void;
  onSelectDrug: (drug: SelectedDrug) => void;
  onClearDrug: () => void;
  protectiveOnly: boolean;
};

type GraphNode = NetworkNode & {
  x?: number;
  y?: number;
  z?: number;
  __label?: SpriteText;
  __labelGroup?: Group;
};

type GraphLink = {
  source: string | GraphNode;
  target: string | GraphNode;
  weight: number;
  sample_ncts: string[];
};

type EdgeFocus = {
  key: string;
  geneName: string;
  drugName: string;
  weight: number;
  ncts: string[];
};

function endpointId(end: string | GraphNode): string {
  return typeof end === "string" ? end : end.id;
}

function endpointName(
  end: string | GraphNode,
  nodesById: Map<string, GraphNode>,
): string {
  if (typeof end !== "string") return end.name;
  return nodesById.get(end)?.name ?? end.replace(/^(gene|drug):/, "");
}

function edgeKey(link: GraphLink): string {
  const a = endpointId(link.source);
  const b = endpointId(link.target);
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function linkToEdgeFocus(
  link: GraphLink,
  nodesById: Map<string, GraphNode>,
): EdgeFocus {
  const sourceId = endpointId(link.source);
  const sourceIsGene = sourceId.startsWith("gene:");
  const geneEnd = sourceIsGene ? link.source : link.target;
  const drugEnd = sourceIsGene ? link.target : link.source;
  return {
    key: edgeKey(link),
    geneName: endpointName(geneEnd, nodesById),
    drugName: endpointName(drugEnd, nodesById),
    weight: link.weight,
    ncts: link.sample_ncts ?? [],
  };
}

function flyToNode(
  fg: ForceGraphMethods<GraphNode, GraphLink>,
  node: GraphNode,
) {
  const x = node.x ?? 0;
  const y = node.y ?? 0;
  const z = node.z ?? 0;
  const dist = 100;
  const hyp = Math.hypot(x, y, z) || 1;
  const ratio = 1 + dist / hyp;
  fg.cameraPosition(
    { x: x * ratio, y: y * ratio, z: z * ratio },
    { x, y, z },
    900,
  );
}

const QUAD_COLOR: Record<Quadrant, string> = {
  validated: "#2dd4bf",
  white_space: "#f59e0b",
  caution: "#eab308",
  deprioritize: "#94a3b8",
};

type GraphCanvasProps = {
  width: number;
  height: number;
  nodes: GraphNode[];
  links: GraphLink[];
  selectedId: string | null;
  focusDrugId: string | null;
  focusEdgeKey: string | null;
  flyToId: string | null;
  flyToToken: number;
  geneById: Map<string, Gene>;
  geneBySymbol: Map<string, Gene>;
  onSelect: (gene: Gene) => void;
  onFocusDrug: (node: GraphNode | null) => void;
  onFocusEdge: (edge: EdgeFocus | null) => void;
  onHoverChange: (node: GraphNode | null) => void;
};

const NetworkCanvas = memo(function NetworkCanvas({
  width,
  height,
  nodes,
  links,
  selectedId,
  focusDrugId,
  focusEdgeKey,
  flyToId,
  flyToToken,
  geneById,
  geneBySymbol,
  onSelect,
  onFocusDrug,
  onFocusEdge,
  onHoverChange,
}: GraphCanvasProps) {
  const fgRef = useRef<ForceGraphMethods<GraphNode, GraphLink> | undefined>(
    undefined,
  );
  const graphData = useMemo(() => ({ nodes, links }), [nodes, links]);
  const nodesById = useMemo(() => {
    const map = new Map<string, GraphNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);
  const hoverIdRef = useRef<string | null>(null);
  const fittedRef = useRef(false);

  useEffect(() => {
    fittedRef.current = false;
  }, [nodes, links]);

  useEffect(() => {
    const fg = fgRef.current;
    if (!fg || nodes.length === 0) return;

    fg.d3Force("charge")?.strength(-220);
    fg.d3Force("link")?.distance(
      (link: GraphLink) => 48 + (4 - Math.min(link.weight, 4)) * 8,
    );
    fg.d3Force("center")?.strength(0.35);

    const controls = fg.controls?.() as
      | {
          enableDamping?: boolean;
          dampingFactor?: number;
          rotateSpeed?: number;
          zoomSpeed?: number;
          panSpeed?: number;
          enablePan?: boolean;
          minDistance?: number;
          maxDistance?: number;
        }
      | undefined;
    if (controls) {
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.rotateSpeed = 0.55;
      controls.zoomSpeed = 0.7;
      controls.panSpeed = 0.7;
      controls.enablePan = true;
      controls.minDistance = 40;
      controls.maxDistance = 1200;
    }
  }, [nodes, links, width, height]);

  const fitCamera = useCallback(() => {
    const fg = fgRef.current;
    if (!fg || fittedRef.current) return;
    fittedRef.current = true;
    fg.zoomToFit(700, 140);
  }, []);

  useEffect(() => {
    if (!flyToId || flyToToken === 0) return;
    const fg = fgRef.current;
    if (!fg) return;

    let tries = 0;
    const attempt = () => {
      const node = nodes.find((n) => n.id === flyToId);
      if (!node) return;
      if (
        node.x == null ||
        node.y == null ||
        node.z == null ||
        Number.isNaN(node.x)
      ) {
        if (tries++ < 40) {
          window.setTimeout(attempt, 50);
        }
        return;
      }
      fittedRef.current = true;
      flyToNode(fg, node);
    };
    attempt();
  }, [flyToId, flyToToken, nodes]);

  const resolveGene = useCallback(
    (node: GraphNode): Gene | null => {
      if (node.kind !== "gene") return null;
      if (node.gene_id && geneById.has(node.gene_id)) {
        return geneById.get(node.gene_id) ?? null;
      }
      if (node.symbol) {
        return geneBySymbol.get(node.symbol.toUpperCase()) ?? null;
      }
      return null;
    },
    [geneById, geneBySymbol],
  );

  return (
    <ForceGraph3D
      ref={fgRef}
      width={width}
      height={height}
      graphData={graphData}
      backgroundColor="#101a1d"
      showNavInfo={false}
      controlType="orbit"
      enableNodeDrag={false}
      enablePointerInteraction
      d3VelocityDecay={0.4}
      d3AlphaDecay={0.08}
      warmupTicks={100}
      cooldownTime={2200}
      cooldownTicks={100}
      onEngineStop={fitCamera}
      nodeId="id"
      linkSource="source"
      linkTarget="target"
      nodeRelSize={5}
      nodeVal={(n) =>
        n.kind === "gene"
          ? 22 + (n.degree || 0) * 2.4
          : 14 + Math.min(n.degree || 0, 6) * 1.5
      }
      nodeOpacity={0.95}
      nodeResolution={16}
      nodeColor={(n) => {
        if (flyToId && n.id === flyToId) return "#f8fafc";
        if (n.kind === "gene") {
          if (selectedId && n.gene_id === selectedId) return "#f8fafc";
          return QUAD_COLOR[(n.quadrant as Quadrant) || "deprioritize"];
        }
        if (focusDrugId === n.id) return "#2dd4bf";
        return "#64748b";
      }}
      linkColor={(l) =>
        focusEdgeKey && edgeKey(l) === focusEdgeKey
          ? "rgba(45, 212, 191, 0.95)"
          : "rgba(45, 212, 191, 0.35)"
      }
      linkWidth={(l) => {
        const base = 1.1 + Math.min(l.weight, 8) * 0.35;
        return focusEdgeKey && edgeKey(l) === focusEdgeKey ? base + 1.4 : base;
      }}
      linkOpacity={0.45}
      linkDirectionalParticles={0}
      linkLabel={(l) => {
        const edge = linkToEdgeFocus(l, nodesById);
        const nctHint =
          edge.ncts.length > 0
            ? edge.ncts.slice(0, 2).join(", ")
            : "no NCT samples";
        return `${edge.geneName} ↔ ${edge.drugName} · ${edge.weight} trials · ${nctHint}`;
      }}
      nodeLabel={(n) =>
        n.kind === "gene"
          ? `${n.name} · ${n.quadrant?.replace("_", " ") || "gene"} · ${n.trial_count} trials`
          : `${n.name} · drug · linked to ${n.degree} genes`
      }
      onNodeHover={(n) => {
        const node = (n as GraphNode) || null;
        const nextId = node?.id ?? null;
        if (hoverIdRef.current === nextId) return;
        hoverIdRef.current = nextId;
        onHoverChange(node);
      }}
      onLinkClick={(l) => {
        onFocusDrug(null);
        onFocusEdge(linkToEdgeFocus(l as GraphLink, nodesById));
      }}
      onBackgroundClick={() => {
        onFocusEdge(null);
      }}
      onNodeClick={(n) => {
        const node = n as GraphNode;
        onFocusEdge(null);
        if (node.kind === "gene") {
          const gene = resolveGene(node);
          if (gene) {
            onFocusDrug(null);
            onSelect(gene);
          }
          return;
        }
        onFocusDrug(node);
      }}
      nodeThreeObjectExtend
      nodeThreeObject={(n) => {
        const node = n as GraphNode;
        if (node.kind !== "gene" && node.kind !== "drug") return false;

        const applyLabelStyle = (label: SpriteText) => {
          // Short display name so long drug strings stay legible
          const raw = node.name;
          const display =
            raw.length > 14 ? `${raw.slice(0, 12)}…` : raw;
          label.text = display;

          const val =
            node.kind === "gene"
              ? 22 + (node.degree || 0) * 2.4
              : 14 + Math.min(node.degree || 0, 6) * 1.5;
          // Match force-graph sphere scale (cbrt(val) * nodeRelSize)
          const radius = Math.cbrt(val) * 5;
          const nameLen = Math.max(display.length, 3);
          // Fill most of the node diameter; shrink only for long names
          const textHeight = Math.max(
            4.2,
            Math.min(radius * 0.72, (radius * 1.65) / nameLen),
          );

          label.color = node.kind === "gene" ? "#1e1233" : "#0f172a";
          label.textHeight = textHeight;
          label.fontWeight = "700";
          label.backgroundColor =
            node.kind === "gene"
              ? "rgba(216, 196, 245, 0.96)"
              : "rgba(226, 212, 248, 0.96)";
          label.padding = Math.max(0.8, textHeight * 0.18);
          label.borderRadius = 2;
          label.strokeWidth = 0.2;
          label.strokeColor = "rgba(15, 23, 42, 0.4)";
          label.position.set(0, 0, 0);
          label.renderOrder = 999;
          if (label.material) {
            label.material.depthTest = false;
            label.material.depthWrite = false;
            label.material.transparent = true;
          }
        };

        if (node.__labelGroup && node.__label) {
          applyLabelStyle(node.__label);
          return node.__labelGroup;
        }

        const group = new Group();
        const label = new SpriteText(node.name);
        applyLabelStyle(label);
        group.add(label);
        node.__label = label;
        node.__labelGroup = group;
        return group;
      }}
    />
  );
});

export function GeneSpace3D({
  genes,
  selectedId,
  onSelect,
  onSelectDrug,
  onClearDrug,
  protectiveOnly,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ width: 0, height: 0 });
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [hover, setHover] = useState<GraphNode | null>(null);
  const [focusDrug, setFocusDrug] = useState<GraphNode | null>(null);
  const [focusEdge, setFocusEdge] = useState<EdgeFocus | null>(null);
  const [query, setQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const [flyToId, setFlyToId] = useState<string | null>(null);
  const [flyToToken, setFlyToToken] = useState(0);

  const geneById = useMemo(() => {
    const map = new Map<string, Gene>();
    genes.forEach((g) => map.set(g.id, g));
    return map;
  }, [genes]);

  const geneBySymbol = useMemo(() => {
    const map = new Map<string, Gene>();
    genes.forEach((g) => map.set(g.symbol.toUpperCase(), g));
    return map;
  }, [genes]);

  const resolveGene = useCallback(
    (node: GraphNode): Gene | null => {
      if (node.kind !== "gene") return null;
      if (node.gene_id && geneById.has(node.gene_id)) {
        return geneById.get(node.gene_id) ?? null;
      }
      if (node.symbol) {
        return geneBySymbol.get(node.symbol.toUpperCase()) ?? null;
      }
      return null;
    },
    [geneById, geneBySymbol],
  );

  const connectedGenesForDrug = useCallback(
    (drug: GraphNode): Gene[] => {
      const out: Gene[] = [];
      for (const link of links) {
        const source = endpointId(link.source);
        const target = endpointId(link.target);
        let geneId: string | null = null;
        if (source === drug.id && target.startsWith("gene:")) geneId = target;
        if (target === drug.id && source.startsWith("gene:")) geneId = source;
        if (!geneId) continue;
        const node = nodes.find((n) => n.id === geneId);
        if (!node) continue;
        const gene = resolveGene(node);
        if (gene && !out.some((g) => g.id === gene.id)) out.push(gene);
      }
      return out.sort((a, b) => a.symbol.localeCompare(b.symbol));
    },
    [links, nodes, resolveGene],
  );

  const lockNode = useCallback(
    (node: GraphNode) => {
      setFocusEdge(null);
      setFlyToId(node.id);
      setFlyToToken((t) => t + 1);
      setQuery(node.name);
      setSearchOpen(false);

      if (node.kind === "gene") {
        const gene = resolveGene(node);
        setFocusDrug(null);
        onClearDrug();
        if (gene) onSelect(gene);
        return;
      }

      setFocusDrug(node);
      onSelectDrug({
        id: node.id,
        name: node.name,
        degree: node.degree,
        trial_count: node.trial_count,
        connectedGenes: connectedGenesForDrug(node),
      });
    },
    [
      connectedGenesForDrug,
      onClearDrug,
      onSelect,
      onSelectDrug,
      resolveGene,
    ],
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const measure = () => {
      const rect = el.getBoundingClientRect();
      const width = Math.floor(rect.width);
      const height = Math.floor(rect.height);
      if (width < 40 || height < 40) return;
      setDims((prev) =>
        prev.width === width && prev.height === height
          ? prev
          : { width, height },
      );
    };

    measure();
    const ro = new ResizeObserver(() => {
      requestAnimationFrame(measure);
    });
    ro.observe(el);
    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchNetwork("asthma")
      .then((res) => {
        if (cancelled) return;
        let nextNodes = res.nodes as GraphNode[];
        if (protectiveOnly) {
          const keep = new Set(
            genes
              .filter((g) => g.protective_variant)
              .map((g) => `gene:${g.symbol}`),
          );
          nextNodes = nextNodes.filter(
            (n) => n.kind === "drug" || keep.has(n.id),
          );
          const keepIds = new Set(nextNodes.map((n) => n.id));
          setLinks(
            res.links.filter(
              (l: NetworkLink) =>
                keepIds.has(l.source) && keepIds.has(l.target),
            ) as GraphLink[],
          );
        } else {
          setLinks(res.links as GraphLink[]);
        }
        setNodes(nextNodes);
        setDescription(res.description);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [genes, protectiveOnly]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!searchRef.current?.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return nodes
      .filter((n) => n.name.toLowerCase().includes(q))
      .sort((a, b) => {
        const aStarts = a.name.toLowerCase().startsWith(q) ? 0 : 1;
        const bStarts = b.name.toLowerCase().startsWith(q) ? 0 : 1;
        if (aStarts !== bStarts) return aStarts - bStarts;
        if (a.kind !== b.kind) return a.kind === "gene" ? -1 : 1;
        return a.name.localeCompare(b.name);
      })
      .slice(0, 10);
  }, [nodes, query]);

  useEffect(() => {
    setActiveIdx(0);
  }, [query]);

  // Fly camera when a gene is selected from the side panel (e.g. drug → gene)
  const prevSelectedId = useRef<string | null>(null);
  useEffect(() => {
    if (selectedId === prevSelectedId.current) return;
    prevSelectedId.current = selectedId;
    if (!selectedId) return;
    const node = nodes.find(
      (n) => n.kind === "gene" && n.gene_id === selectedId,
    );
    if (!node) return;
    setFlyToId(node.id);
    setFlyToToken((t) => t + 1);
  }, [selectedId, nodes]);

  const onHoverChange = useCallback((node: GraphNode | null) => {
    setHover(node);
  }, []);

  const onFocusDrug = useCallback(
    (node: GraphNode | null) => {
      setFocusDrug(node);
      if (!node) {
        onClearDrug();
        return;
      }
      setFlyToId(node.id);
      setFlyToToken((t) => t + 1);
      onSelectDrug({
        id: node.id,
        name: node.name,
        degree: node.degree,
        trial_count: node.trial_count,
        connectedGenes: connectedGenesForDrug(node),
      });
    },
    [connectedGenesForDrug, onClearDrug, onSelectDrug],
  );

  const onFocusEdge = useCallback((edge: EdgeFocus | null) => {
    setFocusEdge(edge);
  }, []);

  const handleGeneSelect = useCallback(
    (gene: Gene) => {
      setFocusDrug(null);
      onClearDrug();
      const node = nodes.find(
        (n) => n.kind === "gene" && (n.gene_id === gene.id || n.symbol === gene.symbol),
      );
      if (node) {
        setFlyToId(node.id);
        setFlyToToken((t) => t + 1);
      }
      onSelect(gene);
    },
    [nodes, onClearDrug, onSelect],
  );

  if (loading) {
    return (
      <div className="space3d-shell network-shell" ref={containerRef}>
        <p className="map-state">Loading drug–gene network…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="space3d-shell network-shell" ref={containerRef}>
        <p className="map-state error">
          Could not load network.
          <br />
          <small>{error}</small>
        </p>
      </div>
    );
  }

  const ready = dims.width > 40 && dims.height > 40;

  return (
    <div className="space3d-shell network-shell" ref={containerRef}>
      <div className="network-search" ref={searchRef}>
        <input
          type="search"
          value={query}
          placeholder="Search gene or drug…"
          aria-label="Search gene or drug"
          aria-expanded={searchOpen}
          aria-controls="network-search-results"
          autoComplete="off"
          onChange={(e) => {
            setQuery(e.target.value);
            setSearchOpen(true);
          }}
          onFocus={() => setSearchOpen(true)}
          onKeyDown={(e) => {
            if (!searchOpen && (e.key === "ArrowDown" || e.key === "Enter")) {
              setSearchOpen(true);
            }
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActiveIdx((i) =>
                matches.length ? (i + 1) % matches.length : 0,
              );
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setActiveIdx((i) =>
                matches.length
                  ? (i - 1 + matches.length) % matches.length
                  : 0,
              );
            } else if (e.key === "Enter") {
              e.preventDefault();
              const pick = matches[activeIdx];
              if (pick) lockNode(pick);
            } else if (e.key === "Escape") {
              setSearchOpen(false);
            }
          }}
        />
        {searchOpen && query.trim() && matches.length > 0 && (
          <ul
            id="network-search-results"
            className="network-search-results"
            role="listbox"
          >
            {matches.map((node, idx) => (
              <li key={node.id} role="option" aria-selected={idx === activeIdx}>
                <button
                  type="button"
                  data-active={idx === activeIdx}
                  onMouseEnter={() => setActiveIdx(idx)}
                  onClick={() => lockNode(node)}
                >
                  <span>{node.name}</span>
                  <span className="kind">{node.kind}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {searchOpen && query.trim() && matches.length === 0 && (
          <p className="network-search-empty">No matches in this network</p>
        )}
      </div>

      <p className="space3d-hint">
        Search or click a gene, drug, or edge · drag to orbit · scroll to zoom
      </p>
      <div className="network-legend-float" aria-hidden>
        <span className="nl-gene">Gene</span>
        <span className="nl-drug">Drug</span>
      </div>
      {description && <p className="network-desc">{description}</p>}

      {ready ? (
        <NetworkCanvas
          width={dims.width}
          height={dims.height}
          nodes={nodes}
          links={links}
          selectedId={selectedId}
          focusDrugId={focusDrug?.id ?? null}
          focusEdgeKey={focusEdge?.key ?? null}
          flyToId={flyToId}
          flyToToken={flyToToken}
          geneById={geneById}
          geneBySymbol={geneBySymbol}
          onSelect={handleGeneSelect}
          onFocusDrug={onFocusDrug}
          onFocusEdge={onFocusEdge}
          onHoverChange={onHoverChange}
        />
      ) : (
        <p className="map-state">Preparing network…</p>
      )}

      {(focusEdge || (hover && !focusDrug && !selectedId)) && (
        <div className="network-hover-card">
          {focusEdge && (
            <>
              <strong>
                {focusEdge.geneName} ↔ {focusEdge.drugName}
              </strong>
              <span>
                {focusEdge.weight} connecting trial
                {focusEdge.weight === 1 ? "" : "s"}
              </span>
              {focusEdge.ncts.length > 0 ? (
                <ul className="network-nct-list">
                  {focusEdge.ncts.map((nct) => (
                    <li key={nct}>
                      <a
                        href={`https://clinicaltrials.gov/study/${nct}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {nct}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="muted">No NCT samples on this edge</span>
              )}
              {focusEdge.weight > focusEdge.ncts.length && (
                <span className="muted">
                  Showing {focusEdge.ncts.length} of {focusEdge.weight}
                </span>
              )}
            </>
          )}
          {!focusEdge && hover && (
            <>
              <strong>{hover.name}</strong>
              <span>
                {hover.kind === "gene"
                  ? `${hover.quadrant?.replace("_", " ")} · ${hover.trial_count} trials`
                  : `Drug · ${hover.degree} gene links`}
              </span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
