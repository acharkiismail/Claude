export default function CompassMark({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9.5" stroke="var(--accent)" strokeWidth="1.6" />
      <path d="M15.2 8.8L10.6 10.6L8.8 15.2L13.4 13.4L15.2 8.8Z" fill="var(--accent)" />
      <circle cx="12" cy="12" r="1.2" fill="var(--surface)" stroke="var(--accent)" strokeWidth="0.8" />
    </svg>
  );
}
