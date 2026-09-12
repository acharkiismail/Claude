export default function Intro({ onStart, statementCount, themeCount }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:py-16">
      <p className="text-sm font-medium uppercase tracking-wide text-sky-600 dark:text-sky-400">
        Élection générale québécoise · 5 octobre 2026
      </p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
        Boussole électorale
      </h1>
      <p className="mt-4 text-base leading-relaxed text-slate-600 dark:text-slate-300">
        Découvrez avec quel parti vous partagez le plus d'affinités, à partir de{" "}
        {statementCount} énoncés répartis sur {themeCount} enjeux de la campagne 2026 :
        coût de la vie, santé, éducation, immigration, langue et laïcité, environnement,
        économie, logement, identité nationale et rôle de l'État.
      </p>

      <div className="mt-8 space-y-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Comment ça marche
        </h2>
        <ol className="space-y-3 text-sm text-slate-600 dark:text-slate-300">
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700 dark:bg-sky-900 dark:text-sky-300">1</span>
            <span>Indiquez l'importance que vous accordez à chacun des 10 thèmes (optionnel).</span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700 dark:bg-sky-900 dark:text-sky-300">2</span>
            <span>Répondez à {statementCount} énoncés sur une échelle de 5 points, du désaccord total à l'accord total.</span>
          </li>
          <li className="flex gap-3">
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700 dark:bg-sky-900 dark:text-sky-300">3</span>
            <span>Consultez votre classement d'affinité avec les 5 principaux partis, avec sources à l'appui pour chaque positionnement.</span>
          </li>
        </ol>
      </div>

      <details className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
        <summary className="cursor-pointer font-semibold text-slate-900 dark:text-slate-100">
          Méthodologie et limites
        </summary>
        <div className="mt-3 space-y-2 leading-relaxed">
          <p>
            Les positions des partis ont été établies à partir de leurs plateformes officielles
            2026 lorsqu'elles étaient disponibles, complétées par le bilan législatif (pour la
            CAQ et le PQ) et des déclarations publiques récentes des chefs, avec une source citée
            pour chaque positionnement.
          </p>
          <p>
            L'affinité est calculée par une distance euclidienne pondérée entre vos réponses et
            les positions de chaque parti, normalisée en pourcentage. Les enjeux marqués « pas
            important » sont exclus du calcul; les thèmes auxquels vous accordez plus
            d'importance comptent davantage.
          </p>
          <p>
            Cet outil est une simplification à visée pédagogique, pas un sondage scientifique ni
            un outil de recommandation de vote. Certaines positions, faute de plateforme complète
            publiée, sont déduites de l'orientation générale du parti et sont identifiées comme
            telles dans les sources.
          </p>
        </div>
      </details>

      <button
        type="button"
        onClick={onStart}
        className="mt-8 w-full rounded-xl bg-sky-600 px-6 py-3.5 text-base font-semibold text-white shadow-sm transition-colors hover:bg-sky-700 sm:w-auto"
      >
        Commencer →
      </button>
    </div>
  );
}
