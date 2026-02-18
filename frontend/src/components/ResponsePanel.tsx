import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { ModelResponse } from "../types";

interface Props {
  response: ModelResponse;
  index: number;
}

const accentColors = ["var(--accent)", "var(--accent-secondary)"];
const ease = [0.22, 1, 0.36, 1] as const;

export function ResponsePanel({ response, index }: Props) {
  const [showDetails, setShowDetails] = useState(false);
  const accent = accentColors[index % 2];

  return (
    <div
      className="panel"
      style={{ "--panel-accent": accent } as React.CSSProperties}
    >
      <div className="panel__accent-line" />

      <div className="panel__header">
        <h3 className="panel__model-name">{response.model_name}</h3>
        {response.was_revised ? (
          <span className="panel__badge panel__badge--revised">
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Revised
          </span>
        ) : (
          <span className="panel__badge panel__badge--unchanged">
            Unchanged
          </span>
        )}
      </div>

      <div className="panel__section">
        <h4 className="panel__section-title">Final Response</h4>
        <div className="panel__content">{response.final_response}</div>
      </div>

      <button
        className="panel__toggle"
        onClick={() => setShowDetails(!showDetails)}
        aria-expanded={showDetails}
      >
        <svg
          className={`panel__toggle-icon ${showDetails ? "panel__toggle-icon--open" : ""}`}
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
        {showDetails ? "Hide" : "View"} deliberation process
      </button>

      <AnimatePresence>
        {showDetails && (
          <motion.div
            className="panel__details"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.35, ease }}
            style={{ overflow: "hidden" }}
          >
            <div className="panel__details-inner">
              <div className="panel__detail-block">
                <h4 className="panel__section-title">Initial Response</h4>
                <div className="panel__content">
                  {response.initial_response}
                </div>
              </div>
              <div className="panel__detail-block">
                <h4 className="panel__section-title">Critique Received</h4>
                <div className="panel__content">
                  {response.critique_received}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
