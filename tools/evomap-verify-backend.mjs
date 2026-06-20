import { spawnSync } from "node:child_process";

const python = process.env.PYTHON || "python3";
const args = [
  "-m",
  "pytest",
  "-q",
  "tests/test_evomap_hashing.py",
  "tests/test_evomap_assets.py",
  "tests/test_evomap_client.py",
];

const result = spawnSync(python, args, {
  cwd: process.cwd(),
  encoding: "utf8",
  stdio: "inherit",
});

process.exit(result.status ?? 1);
