import { partyColor } from "../lib/colors";

const SIZE = 320;
const PAD = 34;

function toSvg(x, y) {
  const usable = SIZE - PAD * 2;
  return {
    cx: PAD + ((x + 1) / 2) * usable,
    cy: PAD + ((1 - y) / 2) * usable,
  };
}

export default function CompassChart({ userPosition, partyPositions }) {
  const user = toSvg(userPosition.economic, userPosition.identity);

  return (
    <div className="w-full">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="mx-auto w-full max-w-sm"
        role="img"
        aria-label="Positionnement sur deux axes : économique et identité nationale"
      >
        <line x1={PAD} y1={SIZE / 2} x2={SIZE - PAD} y2={SIZE / 2} stroke="var(--hairline)" strokeWidth="1" />
        <line x1={SIZE / 2} y1={PAD} x2={SIZE / 2} y2={SIZE - PAD} stroke="var(--hairline)" strokeWidth="1" />
        <rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} fill="none" stroke="var(--hairline)" strokeWidth="1" />

        <text x={SIZE / 2} y={14} textAnchor="middle" className="text-[9px]" style={{ fill: "var(--ink-muted)" }}>
          Souverainiste
        </text>
        <text x={SIZE / 2} y={SIZE - 6} textAnchor="middle" className="text-[9px]" style={{ fill: "var(--ink-muted)" }}>
          Fédéraliste
        </text>
        <text x={8} y={SIZE / 2 + 3} textAnchor="start" className="text-[9px]" style={{ fill: "var(--ink-muted)" }}>
          État
        </text>
        <text x={SIZE - 8} y={SIZE / 2 + 3} textAnchor="end" className="text-[9px]" style={{ fill: "var(--ink-muted)" }}>
          Marché
        </text>

        {partyPositions.map(({ party, position }) => {
          const { cx, cy } = toSvg(position.economic, position.identity);
          return (
            <g key={party.id}>
              <circle cx={cx} cy={cy} r={9} fill={partyColor(party)} stroke="var(--surface)" strokeWidth="1.5" />
              <text
                x={cx}
                y={cy - 13}
                textAnchor="middle"
                className="text-[10px] font-semibold"
                style={{ fill: "var(--ink-secondary)" }}
              >
                {party.shortName}
              </text>
            </g>
          );
        })}

        <rect
          x={user.cx - 6}
          y={user.cy - 6}
          width={12}
          height={12}
          transform={`rotate(45 ${user.cx} ${user.cy})`}
          fill="var(--ink)"
          stroke="var(--surface)"
          strokeWidth="2"
        />
        <text
          x={user.cx}
          y={user.cy + 22}
          textAnchor="middle"
          className="text-[10px] font-bold"
          style={{ fill: "var(--ink)" }}
        >
          Vous
        </text>
      </svg>
      <p className="mt-2 text-center text-xs text-[var(--ink-muted)]">
        Vue simplifiée sur deux axes prédéfinis, calculée à partir des énoncés liés à chaque
        dimension. Le profil par enjeu ci-dessus reste la vue la plus complète.
      </p>
    </div>
  );
}
