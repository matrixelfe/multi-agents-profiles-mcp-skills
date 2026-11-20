import type { Plugin } from "@opencode-ai/plugin";
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const PYTHON_HOOK = join(
  homedir(),
  ".agents",
  "catalog",
  "skills",
  "continuous-learning-v2",
  "scripts",
  "cross-agent-hook.py",
);

function runHook(phase: "pre" | "post", payload: unknown) {
  try {
    const child = spawn("python", [PYTHON_HOOK, phase], {
      windowsHide: true,
      stdio: ["pipe", "ignore", "ignore"],
    });
    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  } catch {
    // Fail-open: never block agent tool execution on observation errors
  }
}

export const ContinuousLearningPlugin: Plugin = async ({ directory }) => {
  return {
    "tool.execute.before": async (input, output) => {
      runHook("pre", {
        cwd: directory,
        tool: input.tool,
        args: output?.args,
      });
    },
    "tool.execute.after": async (input, output) => {
      runHook("post", {
        cwd: directory,
        tool: input.tool,
        output: output?.output,
      });
    },
  } as any;
};

export default ContinuousLearningPlugin;
