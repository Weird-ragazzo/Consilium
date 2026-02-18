import type { Phase } from "../types";

interface Props {
  phase: Phase;
}

const STEPS = [
  { key: "generating", label: "Generate", number: "I" },
  { key: "critiquing", label: "Critique", number: "II" },
  { key: "revising", label: "Revise", number: "III" },
] as const;

type StepKey = (typeof STEPS)[number]["key"];

function getStepState(
  stepKey: StepKey,
  phase: Phase
): "inactive" | "active" | "complete" {
  const order: StepKey[] = ["generating", "critiquing", "revising"];
  const stepIndex = order.indexOf(stepKey);
  const phaseIndex = order.indexOf(phase as StepKey);

  if (phase === "done") return "complete";
  if (phase === "error" || phase === "idle") return "inactive";
  if (stepIndex < phaseIndex) return "complete";
  if (stepIndex === phaseIndex) return "active";
  return "inactive";
}

export function PhaseIndicator({ phase }: Props) {
  if (phase === "idle") return null;

  return (
    <div className="stepper">
      <div className="stepper__track">
        {STEPS.map((step, i) => {
          const state = getStepState(step.key, phase);
          return (
            <div key={step.key} className="stepper__step-wrapper">
              {i > 0 && (
                <div
                  className={`stepper__connector ${
                    state === "complete" || state === "active"
                      ? "stepper__connector--filled"
                      : ""
                  }`}
                />
              )}
              <div className={`stepper__step stepper__step--${state}`}>
                <div className="stepper__circle">
                  {state === "complete" ? (
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : (
                    <span className="stepper__number">{step.number}</span>
                  )}
                </div>
                <span className="stepper__label">{step.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {phase === "error" && (
        <div className="stepper__error">
          <span className="stepper__error-icon">!</span>
          An error occurred during deliberation.
        </div>
      )}
    </div>
  );
}
