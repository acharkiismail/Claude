export default function ReliabilityBadge({ reliability }) {
  const isSourced = reliability === "sourced";
  return (
    <span
      className="inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
      style={{
        color: isSourced ? "var(--status-good)" : "var(--status-warning)",
        backgroundColor: isSourced ? "color-mix(in srgb, var(--status-good) 14%, transparent)" : "color-mix(in srgb, var(--status-warning) 16%, transparent)",
      }}
      title={
        isSourced
          ? "Position directement appuyée par une source (plateforme, bilan ou déclaration)."
          : "Position déduite de l'orientation générale du parti, faute d'engagement chiffré ou de déclaration explicite trouvée."
      }
    >
      <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true">
        {isSourced ? (
          <path d="M1 4.2L3 6.2L7 1.8" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        ) : (
          <path d="M4 0.8L7.5 7H0.5L4 0.8Z" fill="none" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round" />
        )}
      </svg>
      {isSourced ? "Sourcé" : "Déduit"}
    </span>
  );
}
