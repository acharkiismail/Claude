import { useMemo, useState } from "react";
import statements from "./data/statements.json";
import themes from "./data/themes.json";
import parties from "./data/parties.json";
import Header from "./components/Header";
import Intro from "./components/Intro";
import ThemeWeighting from "./components/ThemeWeighting";
import Questionnaire from "./components/Questionnaire";
import Results from "./components/Results";
import { selectShortStatements } from "./lib/scoring";
import { clearHash, readResultFromHash, decodeResult } from "./lib/shareLink";

const STEPS = { INTRO: "intro", WEIGHTING: "weighting", QUIZ: "quiz", RESULTS: "results" };
const STEP_ORDER = [STEPS.INTRO, STEPS.WEIGHTING, STEPS.QUIZ, STEPS.RESULTS];

const defaultWeights = Object.fromEntries(themes.map((t) => [t.id, 1]));
const themesById = Object.fromEntries(themes.map((t) => [t.id, t]));
const partiesById = Object.fromEntries(parties.map((p) => [p.id, p]));
const shortStatements = selectShortStatements(statements, 8);

// Un lien partagé porte les réponses de son auteur : l'app démarre directement sur
// son résultat, avec un bandeau invitant le visiteur à faire le sien.
function sharedResultFromUrl() {
  const encoded = readResultFromHash();
  return encoded ? decodeResult(encoded, statements, themes) : null;
}

export default function App() {
  const [sharedResult] = useState(sharedResultFromUrl);
  const [step, setStep] = useState(sharedResult ? STEPS.RESULTS : STEPS.INTRO);
  const [mode, setMode] = useState("full");
  const [weights, setWeights] = useState(sharedResult?.weights ?? defaultWeights);
  const [answers, setAnswers] = useState(sharedResult?.answers ?? {});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [viewingSharedResult, setViewingSharedResult] = useState(Boolean(sharedResult));

  const activeStatements = useMemo(
    () => (mode === "short" ? shortStatements : statements),
    [mode]
  );

  const handleAnswer = (statementId, value) => {
    setAnswers((prev) => ({ ...prev, [statementId]: value ?? null }));
  };

  const start = (nextMode) => {
    setMode(nextMode);
    setAnswers({});
    setCurrentIndex(0);
    setStep(nextMode === "short" ? STEPS.QUIZ : STEPS.WEIGHTING);
  };

  const restart = () => {
    clearHash();
    setViewingSharedResult(false);
    setAnswers({});
    setWeights(defaultWeights);
    setCurrentIndex(0);
    setStep(STEPS.INTRO);
  };

  return (
    <div className="min-h-dvh" style={{ backgroundColor: "var(--page)" }}>
      <Header stepIndex={STEP_ORDER.indexOf(step)} stepCount={STEP_ORDER.length} />

      {step === STEPS.INTRO && (
        <Intro
          statementCount={statements.length}
          shortCount={shortStatements.length}
          themeCount={themes.length}
          onStart={start}
        />
      )}

      {step === STEPS.WEIGHTING && (
        <ThemeWeighting
          themes={themes}
          weights={weights}
          onChange={(themeId, value) => setWeights((prev) => ({ ...prev, [themeId]: value }))}
          onContinue={() => setStep(STEPS.QUIZ)}
          onSkip={() => {
            setWeights(defaultWeights);
            setStep(STEPS.QUIZ);
          }}
        />
      )}

      {step === STEPS.QUIZ && (
        <Questionnaire
          statements={activeStatements}
          themesById={themesById}
          answers={answers}
          currentIndex={currentIndex}
          onAnswer={handleAnswer}
          onNext={() => setCurrentIndex((i) => Math.min(i + 1, activeStatements.length - 1))}
          onBack={() => setCurrentIndex((i) => Math.max(i - 1, 0))}
          onFinish={() => setStep(STEPS.RESULTS)}
        />
      )}

      {step === STEPS.RESULTS && (
        <Results
          statements={statements}
          themes={themes}
          parties={parties}
          partiesById={partiesById}
          answers={answers}
          weights={weights}
          mode={mode}
          viewingSharedResult={viewingSharedResult}
          onRestart={restart}
          onContinueFull={() => {
            setMode("full");
            setViewingSharedResult(false);
            clearHash();
            const firstUnanswered = statements.findIndex((s) => answers[s.id] === undefined);
            setCurrentIndex(firstUnanswered === -1 ? 0 : firstUnanswered);
            setStep(STEPS.QUIZ);
          }}
        />
      )}
    </div>
  );
}
