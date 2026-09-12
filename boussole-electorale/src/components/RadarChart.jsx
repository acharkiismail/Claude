const SIZE = 320;
const CENTER = SIZE / 2;
const RADIUS = SIZE / 2 - 62;
const RINGS = [25, 50, 75, 100];

function wrapLabel(label) {
  if (label.length <= 11 || !label.includes(" ")) return [label];
  const words = label.split(" ");
  const mid = Math.ceil(words.length / 2);
  return [words.slice(0, mid).join(" "), words.slice(mid).join(" ")];
}

function pointFor(index, count, value) {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count;
  const r = (Math.max(0, Math.min(100, value)) / 100) * RADIUS;
  return { x: CENTER + r * Math.cos(angle), y: CENTER + r * Math.sin(angle) };
}

function polygonPoints(values, count) {
  return values.map((v, i) => pointFor(i, count, v ?? 0)).map((p) => `${p.x},${p.y}`).join(" ");
}

/**
 * Radar/spider chart à la smartspider : un score 0-100 par axe (ici, un thème
 * de l'élection). Affiche le profil de l'utilisateur (contour neutre, jamais une
 * teinte catégorielle) et, optionnellement, celui d'un parti (aplat coloré).
 */
export default function RadarChart({ axes, userValues, party, partyValues, size = "full" }) {
  const count = axes.length;
  const showLabels = size === "full";
  const userPoints = polygonPoints(userValues, count);
  const partyPoints = partyValues ? polygonPoints(partyValues, count) : null;

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      className="mx-auto w-full"
      style={{ maxWidth: showLabels ? 380 : 220 }}
      role="img"
      aria-label={
        party
          ? `Profil par enjeu : vous comparé à ${party.name}`
          : "Votre profil par enjeu"
      }
    >
      {RINGS.map((ring) => (
        <polygon
          key={ring}
          points={polygonPoints(Array(count).fill(ring), count)}
          fill="none"
          stroke="var(--hairline)"
          strokeWidth={1}
        />
      ))}

      {axes.map((axis, i) => {
        const outer = pointFor(i, count, 100);
        return (
          <line
            key={axis.id}
            x1={CENTER}
            y1={CENTER}
            x2={outer.x}
            y2={outer.y}
            stroke="var(--hairline)"
            strokeWidth={1}
          />
        );
      })}

      {partyPoints && (
        <polygon
          points={partyPoints}
          fill={`var(${party.colorVar})`}
          fillOpacity={0.22}
          stroke={`var(${party.colorVar})`}
          strokeWidth={2}
        />
      )}

      <polygon
        points={userPoints}
        fill="none"
        stroke="var(--ink)"
        strokeWidth={2}
        strokeDasharray="4 3"
      />
      {userValues.map((v, i) => {
        const p = pointFor(i, count, v ?? 0);
        return (
          <rect
            key={i}
            x={p.x - 3}
            y={p.y - 3}
            width={6}
            height={6}
            transform={`rotate(45 ${p.x} ${p.y})`}
            fill="var(--ink)"
            stroke="var(--surface)"
            strokeWidth={1}
          />
        );
      })}

      {showLabels &&
        axes.map((axis, i) => {
          const label = pointFor(i, count, 128);
          const anchor = label.x < CENTER - 8 ? "end" : label.x > CENTER + 8 ? "start" : "middle";
          const lines = wrapLabel(axis.shortName);
          return (
            <text
              key={axis.id}
              x={label.x}
              y={label.y}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="fill-current text-[9px] font-medium"
              style={{ fill: "var(--ink-secondary)" }}
            >
              {lines.map((line, li) => (
                <tspan key={li} x={label.x} dy={li === 0 ? (lines.length > 1 ? "-0.35em" : 0) : "1.1em"}>
                  {line}
                </tspan>
              ))}
            </text>
          );
        })}
    </svg>
  );
}
