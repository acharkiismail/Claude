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
  return values
    .map((v, i) => pointFor(i, count, v))
    .map((p) => `${p.x},${p.y}`)
    .join(" ");
}

/**
 * Radar façon "smartspider" : un axe par thème, une valeur 0-100 par axe.
 * Ici la valeur est l'affinité entre l'utilisateur et UN parti sur ce thème —
 * 100 = réponses identiques, 0 = opposition maximale sur tous les énoncés du thème.
 */
export default function RadarChart({ axes, values, color, label, size = "full" }) {
  const count = axes.length;
  const showLabels = size === "full";
  const points = polygonPoints(values, count);

  return (
    <svg
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      className="mx-auto w-full"
      style={{ maxWidth: showLabels ? 380 : 240 }}
      role="img"
      aria-label={label}
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

      <polygon points={points} fill={color} fillOpacity={0.24} stroke={color} strokeWidth={2} />

      {values.map((v, i) => {
        const p = pointFor(i, count, v);
        return (
          <circle
            key={axes[i].id}
            cx={p.x}
            cy={p.y}
            r={3.2}
            fill={color}
            stroke="var(--surface)"
            strokeWidth={1}
          />
        );
      })}

      {showLabels && (
        <text
          x={CENTER + 4}
          y={CENTER - RADIUS + 3}
          className="text-[8px]"
          style={{ fill: "var(--ink-muted)" }}
        >
          100
        </text>
      )}

      {showLabels &&
        axes.map((axis, i) => {
          const anchorPoint = pointFor(i, count, 128);
          const anchor =
            anchorPoint.x < CENTER - 8 ? "end" : anchorPoint.x > CENTER + 8 ? "start" : "middle";
          const lines = wrapLabel(axis.shortName);
          return (
            <text
              key={axis.id}
              x={anchorPoint.x}
              y={anchorPoint.y}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="text-[9px] font-medium"
              style={{ fill: "var(--ink-secondary)" }}
            >
              {lines.map((line, li) => (
                <tspan
                  key={line}
                  x={anchorPoint.x}
                  dy={li === 0 ? (lines.length > 1 ? "-0.35em" : 0) : "1.1em"}
                >
                  {line}
                </tspan>
              ))}
            </text>
          );
        })}
    </svg>
  );
}
