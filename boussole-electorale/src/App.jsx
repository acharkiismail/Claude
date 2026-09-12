import { useState } from "react";
import statements from "./data/statements.json";
import themes from "./data/themes.json";
import parties from "./data/parties.json";
import Header from "./components/Header";
import Intro from "./components/Intro";
import ThemeWeighting from "./components/ThemeWeighting";
import Questionnaire from "./components/Questionnaire";
import Results from "./components/Results";

const STEPS = { INTRO: "intro", WEIGHTING: "weighting", QUIZ: "quiz", RESULTS: "results" };
const STEP_ORDER = [STEPS.INTRO, STEPS.WEIGHTING, STEPS.QUIZ, STEPS.RESULTS];

const defaultWeights = Object.fromEntries(themes.map((t) => [t.id, 1]));
const themesById = Object.fromEntries(themes.map((t) => [t.id, t]));
const partiesById = Object.fromEntries(parties.map((p) => [p.id, p]));

export default function App() {
  const [step, setStep] = useState(STEPS.INTRO);
  const [weights, setWeights] = useState(defaultWeights);
  const [answers, setAnswers] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleAnswer = (statementId, value) => {
    setAnswers((prev) => {
      if (value == null) {
        const next = { ...prev };
        next[statementId] = null;
        return next;
      }
      return { ...prev, [statementId]: value };
    });
  };

  const restart = () => {
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
          themeCount={themes.length}
          onStart={() => setStep(STEPS.WEIGHTING)}
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
          statements={statements}
          themesById={themesById}
          answers={answers}
          currentIndex={currentIndex}
          onAnswer={handleAnswer}
          onNext={() => setCurrentIndex((i) => Math.min(i + 1, statements.length - 1))}
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
          onRestart={restart}
        />
      )}
    </div>
  );
}
