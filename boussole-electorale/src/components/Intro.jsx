export default function Intro({ onStart, statementCount, themeCount }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:py-16 sm:px-6">
      <p className="text-sm font-semibold uppercase tracking-wide" style={{ color: "var(--accent)" }}>
        Élection générale québécoise · 5 octobre 2026
      </p>
      <h1 className="font-display mt-3 text-4xl font-semibold leading-[1.05] tracking-tight sm:text-[2.75rem]">
        Avec quel parti partagez-vous le plus d'affinités ?
      </h1>
      <p className="mt-4 text-base leading-relaxed text-[var(--ink-secondary)]">
        {statementCount} énoncés répartis sur {themeCount} enjeux de la campagne 2026 — coût de
        la vie, santé, éducation, immigration, langue et laïcité, environnement, économie,
        logement, identité nationale et rôle de l'État — pour comparer vos positions à celles des
        cinq principaux partis.
      </p>

      <div className="mt-8 space-y-4 rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
        <h2 className="text-sm font-semibold text-[var(--ink)]">Comment ça marche</h2>
        <ol className="space-y-3 text-sm text-[var(--ink-secondary)]">
          <li className="flex gap-3">
            <span
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
              style={{ backgroundColor: "var(--accent-soft)", color: "var(--accent-strong)" }}
            >
              1
            </span>
            <span>Indiquez l'importance que vous accordez à chacun des 10 thèmes (optionnel).</span>
          </li>
          <li className="flex gap-3">
            <span
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
              style={{ backgroundColor: "var(--accent-soft)", color: "var(--accent-strong)" }}
            >
              2
            </span>
            <span>
              Répondez à {statementCount} énoncés sur une échelle de 5 points, du désaccord total
              à l'accord total.
            </span>
          </li>
          <li className="flex gap-3">
            <span
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
              style={{ backgroundColor: "var(--accent-soft)", color: "var(--accent-strong)" }}
            >
              3
            </span>
            <span>
              Consultez votre classement d'affinité, votre profil par enjeu, et les sources
              derrière chaque positionnement.
            </span>
          </li>
        </ol>
      </div>

      <details className="mt-6 rounded-2xl border border-[var(--hairline)] bg-[var(--surface)] p-5 text-sm text-[var(--ink-secondary)]">
        <summary className="cursor-pointer font-semibold text-[var(--ink)]">
          Méthodologie et limites
        </summary>
        <div className="mt-3 space-y-2.5 leading-relaxed">
          <p>
            La démarche s'inspire des outils d'aide au vote les plus rigoureux au monde —
            <strong className="text-[var(--ink)]"> smartvote</strong> (Suisse) et le{" "}
            <strong className="text-[var(--ink)]">Wahl-O-Mat</strong> (Allemagne) — qui
            privilégient des énoncés à fort pouvoir discriminant (sur lesquels les partis
            répondent réellement différemment), un contexte factuel par énoncé, et une
            pondération par thème plutôt qu'un score global unique.
          </p>
          <p>
            Les positions des partis ont été établies à partir de leurs plateformes officielles
            2026 lorsqu'elles étaient disponibles, complétées par le bilan législatif (CAQ, PQ) et
            des déclarations publiques récentes des chefs. Chaque position affiche une source et
            un badge de fiabilité — « Sourcé » (appuyé par une source directe) ou « Déduit »
            (faute d'engagement chiffré trouvé, déduit de l'orientation générale du parti).
          </p>
          <p>
            L'affinité est calculée par une distance euclidienne pondérée entre vos réponses et
            les positions de chaque parti; le profil par enjeu (façon « smartspider ») montre, en
            plus du score global, où vous êtes proche ou loin de chaque parti thème par thème. Cet
            outil est une simplification à visée pédagogique, pas un sondage scientifique ni un
            outil de recommandation de vote.
          </p>
        </div>
      </details>

      <button
        type="button"
        onClick={onStart}
        className="mt-8 w-full rounded-xl px-6 py-3.5 text-base font-semibold shadow-sm transition-transform active:scale-[0.99] sm:w-auto"
        style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
      >
        Commencer →
      </button>
    </div>
  );
}
