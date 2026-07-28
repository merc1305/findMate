import { createHash } from "node:crypto";
import {
  lstat,
  mkdir,
  readFile,
  readdir,
  writeFile,
} from "node:fs/promises";
import { dirname, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { unzipSync, zipSync } from "fflate";

const SITE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SKILL_SOURCE = resolve(
  SITE_ROOT,
  "../skills/find-complementary-founders",
);
const OUTPUT_DIRECTORY = resolve(
  SITE_ROOT,
  "public/.well-known/agent-skills",
);
const ARCHIVE_NAME = "find-complementary-founders.zip";
const FIXED_MTIME = new Date("1980-01-01T00:00:00.000Z");
const DISCOVERY_SCHEMA =
  "https://schemas.agentskills.io/discovery/0.2.0/schema.json";
const DESCRIPTION =
  "Find a complementary human cofounder or project partner. The agent assesses only its own owner, creates a private evidence-based draft first, publishes only the exact privacy-minimized profile the owner approves, and compares it only with profiles other agents published for their own owners.";

const EXPECTED_FILES = [
  "LICENSE.txt",
  "SKILL.md",
  "agents/openai.yaml",
  "references/community-growth.md",
  "references/evidence-model.md",
  "references/example-founder-complement-canvas.md",
  "references/moltbook.md",
  "references/owner-onboarding.ru.md",
  "references/privacy-safety.md",
  "references/profile-schema.md",
  "scripts/assess_profile.py",
  "scripts/github_thread.py",
  "scripts/match_profiles.py",
  "scripts/moltbook_publish.py",
  "scripts/private_report.py",
  "scripts/profile_card.py",
  "scripts/validate_profile.py",
  "scripts/verify_github_submission.py",
];

async function discoverFiles(directory) {
  const discovered = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.name === "__pycache__") {
      continue;
    }
    const absolutePath = resolve(directory, entry.name);
    const metadata = await lstat(absolutePath);
    if (metadata.isSymbolicLink()) {
      throw new Error(
        `Symlinks are not allowed in the discovery archive: ${absolutePath}`,
      );
    }
    if (metadata.isDirectory()) {
      discovered.push(...(await discoverFiles(absolutePath)));
      continue;
    }
    if (!metadata.isFile()) {
      throw new Error(`Unsupported skill entry: ${absolutePath}`);
    }
    discovered.push(relative(SKILL_SOURCE, absolutePath).split(sep).join("/"));
  }
  return discovered.sort();
}

function assertSameFiles(actual) {
  const expected = [...EXPECTED_FILES].sort();
  if (
    actual.length !== expected.length ||
    actual.some((path, index) => path !== expected[index])
  ) {
    throw new Error(
      `Skill discovery allowlist mismatch.\nExpected: ${expected.join(", ")}\nActual: ${actual.join(", ")}`,
    );
  }
}

async function buildArchive() {
  const discovered = await discoverFiles(SKILL_SOURCE);
  assertSameFiles(discovered);

  const entries = {};
  for (const path of EXPECTED_FILES) {
    entries[path] = [
      new Uint8Array(await readFile(resolve(SKILL_SOURCE, path))),
      { level: 0, mtime: FIXED_MTIME },
    ];
  }

  const archive = zipSync(entries, { level: 0 });
  const unpacked = unzipSync(archive);
  assertSameFiles(Object.keys(unpacked).sort());

  for (const path of EXPECTED_FILES) {
    const source = entries[path][0];
    const extracted = unpacked[path];
    if (
      extracted.length !== source.length ||
      extracted.some((byte, index) => byte !== source[index])
    ) {
      throw new Error(`Discovery archive differs from source: ${path}`);
    }
  }
  return archive;
}

async function main() {
  const archive = await buildArchive();
  const digest = createHash("sha256").update(archive).digest("hex");
  const index = {
    $schema: DISCOVERY_SCHEMA,
    skills: [
      {
        name: "find-complementary-founders",
        type: "archive",
        description: DESCRIPTION,
        url: ARCHIVE_NAME,
        digest: `sha256:${digest}`,
      },
    ],
  };

  await mkdir(OUTPUT_DIRECTORY, { recursive: true });
  await Promise.all([
    writeFile(resolve(OUTPUT_DIRECTORY, ARCHIVE_NAME), archive),
    writeFile(
      resolve(OUTPUT_DIRECTORY, "index.json"),
      `${JSON.stringify(index, null, 2)}\n`,
      "utf8",
    ),
  ]);
  process.stdout.write(
    `Built Agent Skills discovery index (${EXPECTED_FILES.length} files, sha256:${digest}).\n`,
  );
}

await main();
