// Carte de résultat 1080×1080, dessinée en canvas côté client : c'est l'objet qui
// circule sur les réseaux. Les couleurs sont figées sur la palette claire plutôt
// que lues dans le thème courant — une image partagée doit avoir la même allure
// pour tout le monde, peu importe le thème de celui qui l'a produite.

const SIZE = 1080;
const PALETTE = {
  surface: "#fcfcfb",
  page: "#f7f6f2",
  ink: "#14140f",
  inkSecondary: "#52514e",
  inkMuted: "#898781",
  hairline: "#e5e3db",
  accent: "#0f766e",
  parties: {
    caq: "#0d9aa8",
    pq: "#2f6be0",
    plq: "#b91c1c",
    qs: "#ef8617",
    pcq: "#14276b",
  },
};

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function wrapText(ctx, text, maxWidth) {
  const words = text.split(" ");
  const lines = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (ctx.measureText(candidate).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function drawRadar(ctx, cx, cy, radius, values, color) {
  const count = values.length;
  if (count < 3) return;
  const point = (i, value) => {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / count;
    const r = (Math.max(0, Math.min(100, value)) / 100) * radius;
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  };

  ctx.strokeStyle = PALETTE.hairline;
  ctx.lineWidth = 2;
  for (const ring of [25, 50, 75, 100]) {
    ctx.beginPath();
    for (let i = 0; i < count; i++) {
      const [x, y] = point(i, ring);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.stroke();
  }
  for (let i = 0; i < count; i++) {
    const [x, y] = point(i, 100);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(x, y);
    ctx.stroke();
  }

  ctx.beginPath();
  for (let i = 0; i < count; i++) {
    const [x, y] = point(i, values[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.globalAlpha = 0.25;
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = color;
  ctx.lineWidth = 5;
  ctx.stroke();

  ctx.fillStyle = color;
  for (let i = 0; i < count; i++) {
    const [x, y] = point(i, values[i]);
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fill();
  }
}

export function drawShareCard(canvas, { topParty, affinity, isTie, runnerUp, ranked, radarValues, closest, furthest }) {
  const ctx = canvas.getContext("2d");
  canvas.width = SIZE;
  canvas.height = SIZE;

  ctx.fillStyle = PALETTE.page;
  ctx.fillRect(0, 0, SIZE, SIZE);
  ctx.fillStyle = PALETTE.surface;
  roundRect(ctx, 40, 40, SIZE - 80, SIZE - 80, 40);
  ctx.fill();

  const partyColor = PALETTE.parties[topParty.id] ?? PALETTE.accent;
  const left = 96;

  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = PALETTE.accent;
  ctx.font = "700 26px Inter, system-ui, sans-serif";
  ctx.fillText("REPÈRE 2026 · ÉLECTION DU 5 OCTOBRE", left, 132);

  ctx.fillStyle = PALETTE.inkSecondary;
  ctx.font = "500 34px Inter, system-ui, sans-serif";
  ctx.fillText(isTie ? "Résultat serré entre" : "Je suis le plus proche", left, 196);

  ctx.fillStyle = partyColor;
  ctx.font = "700 62px Georgia, 'Source Serif 4', serif";
  const headline = isTie
    ? `${topParty.shortName} et ${runnerUp.shortName}`
    : `${topParty.article} ${topParty.name}`;
  const lines = wrapText(ctx, headline, SIZE - left * 2);
  let y = 268;
  for (const line of lines.slice(0, 2)) {
    ctx.fillText(line, left, y);
    y += 70;
  }

  ctx.fillStyle = PALETTE.ink;
  ctx.font = "700 46px Inter, system-ui, sans-serif";
  ctx.fillText(`${affinity.toFixed(0)} % d'affinité`, left, y + 14);

  drawRadar(ctx, SIZE / 2, 660, 185, radarValues, partyColor);

  // Bandeau du bas : le classement compact et l'écart qui raconte quelque chose.
  const barY = 880;
  const barW = (SIZE - left * 2 - 4 * 16) / 5;
  ranked.slice(0, 5).forEach((entry, i) => {
    const x = left + i * (barW + 16);
    const color = PALETTE.parties[entry.party.id] ?? PALETTE.inkMuted;
    ctx.fillStyle = PALETTE.hairline;
    roundRect(ctx, x, barY, barW, 10, 5);
    ctx.fill();
    ctx.fillStyle = color;
    roundRect(ctx, x, barY, Math.max((barW * entry.affinity) / 100, 12), 10, 5);
    ctx.fill();
    ctx.fillStyle = PALETTE.inkSecondary;
    ctx.font = "700 22px Inter, system-ui, sans-serif";
    ctx.fillText(entry.party.shortName, x, barY - 16);
    ctx.fillStyle = PALETTE.inkMuted;
    ctx.font = "500 20px Inter, system-ui, sans-serif";
    ctx.fillText(`${entry.affinity.toFixed(0)}%`, x, barY + 34);
  });

  if (closest && furthest && closest.theme.id !== furthest.theme.id) {
    ctx.fillStyle = PALETTE.inkSecondary;
    ctx.font = "500 26px Inter, system-ui, sans-serif";
    ctx.fillText(
      `Plus proche : ${closest.theme.shortName} ${closest.value} %  ·  Plus loin : ${furthest.theme.shortName} ${furthest.value} %`,
      left,
      962
    );
  }

  ctx.fillStyle = PALETTE.inkMuted;
  ctx.font = "500 24px Inter, system-ui, sans-serif";
  ctx.fillText("Fais le test —", left, 1008);
  ctx.fillStyle = PALETTE.accent;
  ctx.font = "700 24px Inter, system-ui, sans-serif";
  ctx.fillText(window.location.host, left + ctx.measureText("Fais le test — ").width - 24, 1008);
}

export function canvasToBlob(canvas) {
  return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
}
