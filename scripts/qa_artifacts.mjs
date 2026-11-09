// Shared, project-relative output policy for browser QA evidence.
import { mkdir, mkdtemp, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../artifacts/browser/", import.meta.url));
const runs = new Map();

async function runDirectory(suite) {
    if (!runs.has(suite)) {
        runs.set(suite, (async () => {
            const parent = join(root, suite, "runs");
            await mkdir(parent, { recursive: true });
            const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
            const directory = await mkdtemp(join(parent, `${timestamp}-`));
            console.error(`QA artifacts: ${directory}`);
            return directory;
        })());
    }
    return runs.get(suite);
}

export async function writeBrowserArtifact(suite, kind, name, content) {
    const directory = join(await runDirectory(suite), kind);
    await mkdir(directory, { recursive: true });
    await writeFile(join(directory, name), content);
}
