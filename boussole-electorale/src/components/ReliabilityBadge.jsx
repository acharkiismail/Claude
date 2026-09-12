const VARIANTS = {
  sourced: {
    label: "Sourcé",
    color: "var(--status-good)",
    title: "Position directement appuyée par une source (plateforme, bilan législatif ou déclaration).",
  },
  inferred: {
    label: "Déduit",
    color: "var(--status-warning)",
    title:
      "Position déduite d'un engagement connexe ou de l'orientation générale du parti, faute d'engagement chiffré explicite.",
  },
  unknown: {
    label: "Non documenté",
    color: "var(--ink-muted)",
    title:
      "Aucune position trouvée sur cet énoncé. L'énoncé est exclu du calcul d'affinité pour ce parti, plutôt que d'être compté comme une position neutre.",
  },
};

export default function ReliabilityBadge({ reliability }) {
  const variant = VARIANTS[reliability] ?? VARIANTS.inferred;

  return (
    <span
      className="inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
      style={{
        color: variant.color,
        backgroundColor: `color-mix(in srgb, ${variant.color} 15%, transparent)`,
      }}
      title={variant.title}
    >
      <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true">
        {reliability === "sourced" && (
          <path
            d="M1 4.2L3 6.2L7 1.8"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}
        {reliability === "inferred" && (
          <path d="M4 0.8L7.5 7H0.5L4 0.8Z" fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round" />
        )}
        {reliability === "unknown" && (
          <circle cx="4" cy="4" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.1" strokeDasharray="1.6 1.4" />
        )}
      </svg>
      {variant.label}
    </span>
  );
}
