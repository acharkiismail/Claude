import { citationSearchUrl } from "../lib/citation";

export default function SourceLine({ source, citation }) {
  const url = citationSearchUrl(citation, source);

  return (
    <span className="text-[var(--ink-muted)]">
      {source}
      {citation && (
        <>
          {" "}
          {url ? (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-0.5 whitespace-nowrap rounded px-1 font-medium underline decoration-dotted underline-offset-2 hover:decoration-solid"
              style={{ color: "var(--accent)" }}
              title={`Rechercher : ${citation}`}
            >
              {citation}
              <svg width="8" height="8" viewBox="0 0 8 8" aria-hidden="true" className="shrink-0">
                <path
                  d="M2.4 1h4.6v4.6M7 1L1 7"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
          ) : (
            <span className="whitespace-nowrap font-medium">{citation}</span>
          )}
        </>
      )}
    </span>
  );
}
