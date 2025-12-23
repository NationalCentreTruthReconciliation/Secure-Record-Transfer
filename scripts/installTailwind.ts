/**
 * Install Tailwind standalone CLI.
 */
import { existsSync, mkdirSync, readdirSync, unlinkSync, chmodSync } from "node:fs";
import path from "node:path";
import { parseArgs } from "util";

const { values, positionals } = parseArgs({
    args: Bun.argv,
    options: {
        "clean": {
            type: "boolean",
        },
    },
    strict: true,
    allowPositionals: true,
});

const version = positionals[2];

if (!version) {
    console.error("Must specify the Tailwind version (e.g., v4.1.18)");
    process.exit(1);
}

if (!version.startsWith("v")) {
    console.error("Version must start with 'v' (e.g., v4.1.18)");
    process.exit(1);
}

const TOOLS_DIR = path.join(path.dirname(import.meta.dir), "tools");

if (!existsSync(TOOLS_DIR)) {
    mkdirSync(TOOLS_DIR, { recursive: false });
}

/**
 * Get the platform suffix for the current machine.
 * @returns {string} The platform suffix for this host.
 */
function getPlatformSuffix(): string {
    const platform = process.platform;
    const arch = process.arch;

    if (platform === "linux" && arch === "x64") {
        return "linux-x64";
    } else if (platform === "linux" && arch === "arm64") {
        return "linux-arm64";
    } else if (platform === "darwin" && arch === "x64") {
        return "macos-x64";
    } else if (platform === "darwin" && arch === "arm64") {
        return "macos-arm64";
    } else if (platform === "win32" && arch === "x64") {
        return "windows-x64.exe";
    } else if (platform === "win32" && arch === "arm64") {
        return "windows-arm64.exe";
    }
    throw new Error(`Unsupported platform: ${platform}-${arch}`);
}

const platformSuffix = getPlatformSuffix();

const targetName = "win32" === process.platform ? "tailwindcss.exe" : "tailwindcss";
const targetPath = path.join(TOOLS_DIR, targetName);

// Check for existing tailwindcss installations
let existingFiles = readdirSync(TOOLS_DIR).filter(f => f.startsWith("tailwindcss"));

if (values.clean ?? false) {
    for (const file of existingFiles) {
        const filePath = path.join(TOOLS_DIR, file);
        unlinkSync(filePath);
    }

    existingFiles = readdirSync(TOOLS_DIR).filter(f => f.startsWith("tailwindcss"));
}

if (existingFiles.includes(targetName)) {
    console.info("Standalone Tailwind CLI is installed.");
    process.exit(0);
}

// Download the new version
const downloadUrl = `https://github.com/tailwindlabs/tailwindcss/releases/download/${version}/tailwindcss-${platformSuffix}`;
console.info(`Downloading Tailwind CLI ${version} from ${downloadUrl}...`);

const response = await fetch(downloadUrl);

if (!response.ok) {
    console.error(`Failed to download: ${response.status} ${response.statusText}`);
    process.exit(1);
}

const buffer = await response.arrayBuffer();
await Bun.write(targetPath, buffer);

// Make executable on Unix systems
if (process.platform !== "win32") {
    chmodSync(targetPath, 0o755);
}

console.info(`Standalone Tailwind CLI ${version} installed to ${targetPath}`);
