import { motion } from "framer-motion";
import type { CouncilResponse } from "../types";
import { ResponsePanel } from "./ResponsePanel";

interface Props {
  result: CouncilResponse;
}

const ease = [0.22, 1, 0.36, 1] as const;

export function CouncilView({ result }: Props) {
  return (
    <div className="council">
      <div className="council__divider">
        <span className="council__divider-diamond">◆</span>
        <span className="council__divider-text">Council Deliberation</span>
        <span className="council__divider-diamond">◆</span>
      </div>

      <div className="council__grid">
        {[result.model_a, result.model_b].map((model, i) => (
          <motion.div
            key={model.model_id}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.6,
              delay: i * 0.15,
              ease,
            }}
          >
            <ResponsePanel response={model} index={i} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
