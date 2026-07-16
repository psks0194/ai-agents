"""Riskiest-integration spike: can Python get structured lint findings from the
Angular toolchain? If yes, the architecture is viable. If no, rethink tonight."""

import json
import subprocess
from pathlib import Path

APP = Path.home() / "Code" / "ai-agents" / "week8-capstone" / "sample-app"

result = subprocess.run(
    ["npx", "eslint", ".", "--format", "json"],
    cwd=APP,
    capture_output=True,
    text=True,
    timeout=120,
)

# eslint exits non-zero when it finds problems — that's success, not failure.
raw = result.stdout.strip()
if not raw:
    print("No JSON on stdout. stderr:\n", result.stderr[:500])
    raise SystemExit(1)

findings = json.loads(raw)
total = sum(len(f["messages"]) for f in findings)
print(f"Parsed {len(findings)} files, {total} findings.")
for f in findings:
    for m in f["messages"][:3]:
        print(f"  {Path(f['filePath']).name}:{m.get('line')} [{m.get('ruleId')}] {m['message'][:70]}")