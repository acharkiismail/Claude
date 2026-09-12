import { useEffect, useRef, useState } from "react";
import { canvasToBlob, drawShareCard } from "../lib/shareCard";

export default function ShareSection({ cardData, shareUrl }) {
  const canvasRef = useRef(null);
  const [copied, setCopied] = useState(false);
  const [canShareFile] = useState(() => {
    try {
      const probe = new File(["x"], "x.png", { type: "image/png" });
      return Boolean(navigator.canShare?.({ files: [probe] }));
    } catch {
      return false;
    }
  });

  useEffect(() => {
    if (canvasRef.current) drawShareCard(canvasRef.current, cardData);
  }, [cardData]);

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    } catch {
      window.prompt("Copiez ce lien :", shareUrl);
    }
  };

  const downloadImage = async () => {
    const blob = await canvasToBlob(canvasRef.current);
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "mon-resultat-repere-2026.png";
    link.click();
    URL.revokeObjectURL(url);
  };

  const shareNative = async () => {
    const blob = await canvasToBlob(canvasRef.current);
    if (!blob) return;
    const file = new File([blob], "mon-resultat-repere-2026.png", { type: "image/png" });
    try {
      await navigator.share({
        files: [file],
        title: "Mon résultat — Repère 2026",
        text: "Avec quel parti québécois es-tu le plus d'accord ?",
      });
    } catch {
      /* partage annulé par l'utilisateur */
    }
  };

  const buttonClass =
    "rounded-xl px-4 py-2.5 text-sm font-semibold transition-transform active:scale-[0.98]";

  return (
    <div>
      <canvas
        ref={canvasRef}
        className="mx-auto w-full max-w-xs rounded-xl border"
        style={{ borderColor: "var(--hairline)" }}
        aria-label="Aperçu de votre carte de résultat"
      />
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {canShareFile && (
          <button
            type="button"
            onClick={shareNative}
            className={buttonClass}
            style={{ backgroundColor: "var(--accent)", color: "var(--on-accent)" }}
          >
            Partager
          </button>
        )}
        <button
          type="button"
          onClick={downloadImage}
          className={buttonClass}
          style={
            canShareFile
              ? { border: "1px solid var(--hairline)", color: "var(--ink-secondary)" }
              : { backgroundColor: "var(--accent)", color: "var(--on-accent)" }
          }
        >
          Télécharger l'image
        </button>
        <button
          type="button"
          onClick={copyLink}
          className={buttonClass}
          style={{ border: "1px solid var(--hairline)", color: "var(--ink-secondary)" }}
        >
          {copied ? "Lien copié ✓" : "Copier le lien"}
        </button>
      </div>
      <p className="mt-3 text-center text-xs text-[var(--ink-muted)]">
        Le lien contient vos réponses : la personne qui l'ouvre voit votre résultat et peut
        comparer le sien. Rien n'est enregistré sur un serveur.
      </p>
    </div>
  );
}
