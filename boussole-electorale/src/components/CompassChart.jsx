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
        <line x1={PAD} y1={SIZE / 2} x2={SIZE - PAD} y2={SIZE / 2} className="stroke-slate-300 dark:stroke-slate-700" strokeWidth="1" />
        <line x1={SIZE / 2} y1={PAD} x2={SIZE / 2} y2={SIZE - PAD} className="stroke-slate-300 dark:stroke-slate-700" strokeWidth="1" />
        <rect x={PAD} y={PAD} width={SIZE - PAD * 2} height={SIZE - PAD * 2} fill="none" className="stroke-slate-200 dark:stroke-slate-800" strokeWidth="1" />

        <text x={SIZE / 2} y={14} textAnchor="middle" className="fill-slate-500 text-[9px] dark:fill-slate-400">
          Souverainiste
        </text>
        <text x={SIZE / 2} y={SIZE - 6} textAnchor="middle" className="fill-slate-500 text-[9px] dark:fill-slate-400">
          Fédéraliste
        </text>
        <text x={8} y={SIZE / 2 + 3} textAnchor="start" className="fill-slate-500 text-[9px] dark:fill-slate-400">
          État
        </text>
        <text x={SIZE - 8} y={SIZE / 2 + 3} textAnchor="end" className="fill-slate-500 text-[9px] dark:fill-slate-400">
          Marché
        </text>

        {partyPositions.map(({ party, position }) => {
          const { cx, cy } = toSvg(position.economic, position.identity);
          return (
            <g key={party.id}>
              <circle cx={cx} cy={cy} r={9} fill={party.color} stroke="white" strokeWidth="1.5" />
              <text
                x={cx}
                y={cy - 13}
                textAnchor="middle"
                className="fill-slate-700 text-[10px] font-semibold dark:fill-slate-200"
              >
                {party.shortName}
              </text>
            </g>
          );
        })}

        <circle cx={user.cx} cy={user.cy} r={7} className="fill-slate-900 dark:fill-white" stroke="white" strokeWidth="2" />
        <text
          x={user.cx}
          y={user.cy + 21}
          textAnchor="middle"
          className="fill-slate-900 text-[10px] font-bold dark:fill-white"
        >
          Vous
        </text>
      </svg>
      <p className="mt-2 text-center text-xs text-slate-500 dark:text-slate-400">
        Positionnement simplifié sur deux axes prédéfinis, calculé à partir des énoncés liés à
        chaque dimension. Ne représente pas la totalité des 10 enjeux.
      </p>
    </div>
  );
}
