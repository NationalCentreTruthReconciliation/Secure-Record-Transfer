/**
 * Build Javascript assets with Bun and CSS assets with the Tailwind CLI.
 *
 * Activate watched mode with --watch
 * Clean dist/ dir before building with --clean
 *
 * Generates JSON stats to mimic webpack-bundle-tracker. See: https://www.npmjs.com/package/webpack-bundle-tracker
 */
import { createHash } from "node:crypto";
import {
    chmodSync,
    existsSync,
    mkdirSync,
    readdirSync,
    rmSync,
    watch,
    writeFileSync,
} from "node:fs";
import path from "node:path";
import { parseArgs } from "util";
import { build } from "bun";

const { values } = parseArgs({
    args: Bun.argv,
    options: {
        "clean": {
            type: "boolean",
        },
        "watch": {
            type: "boolean",
        },
        "only-tailwind": {
            type: "boolean",
        },
    },
    strict: true,
    allowPositionals: true,
});

const isProd = process.env.NODE_ENV === "production";

const TOOLS_DIR = path.join(import.meta.dir, "tools");
const TAILWIND_VERSION = process.env.TAILWIND_VERSION?? "v4.1.18";
const TAILWIND_EXECUTABLE = path.join(
    TOOLS_DIR,
    "win32" === process.platform ? "tailwindcss.exe" : "tailwindcss"
);

const JS_ENTRYPOINTS: Record<string, string> = {
    app: path.join(import.meta.dir, "app/frontend/admin/admin.ts"),
    admin: path.join(import.meta.dir, "app/frontend/app/app.ts"),
};

const CSS_ENTRYPOINTS: Record<string, string> = {
    app: path.join(import.meta.dir, "app/frontend/app/main.css"),
    admin: path.join(import.meta.dir, "app/frontend/admin/main.css"),
};

const DIST_DIR = path.join(import.meta.dir, "dist");
const WATCH_DIR = path.join(import.meta.dir, "app/frontend");
const WATCHED_ASSETS = [".js", ".ts", ".css"];
const DEBOUNCE_MS = 300;

const STATIC_URL = "/static/";
const STATS_FILE = path.join(import.meta.dir, "dist/webpack-stats.json");

interface BuildOptions {
    clean: boolean,
    production: boolean,
};

// A simplified version of Bun.BuildArtifact
interface Artifact {
    kind: string,
    path: string,
    hash: string | null,
}

interface AssetEntry {
    name: string;
    publicPath: string;
    path: string;
}

interface WebpackStats {
    status: string;
    assets: Record<string, AssetEntry>;
    chunks: Record<string, string[]>;
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

/**
 * Install standalone Tailwind CLI if it is not already installed.
 * @returns {Promise<boolean>} true if Tailwind is/was installed, false if not or if some error
 * occurred
 */
async function ensureTailwindInstalled(): Promise<boolean> {
    if (!existsSync(TOOLS_DIR)) {
        mkdirSync(TOOLS_DIR, { recursive: false });
    }

    const targetName = path.basename(TAILWIND_EXECUTABLE);
    const targetPath = path.join(TOOLS_DIR, targetName);
    const existingFiles = readdirSync(TOOLS_DIR).filter(f => f.startsWith("tailwindcss"));

    if (existingFiles.includes(targetName)) {
        return true;
    }

    const platformSuffix = getPlatformSuffix();
    const downloadUrl = `https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-${platformSuffix}`;
    console.info(`Downloading Tailwind CLI ${TAILWIND_VERSION} from ${downloadUrl}...`);

    const response = await fetch(downloadUrl);

    if (!response.ok) {
        console.error(`Failed to download: ${response.status} ${response.statusText}`);
        return false;
    }

    const buffer = await response.arrayBuffer();
    await Bun.write(targetPath, buffer);

    // Make executable on Unix systems
    if (process.platform !== "win32") {
        chmodSync(targetPath, 0o755);
    }

    console.info(`Standalone Tailwind CLI ${TAILWIND_VERSION} installed to ${targetPath}`);
    return true;
}

/**
 * Build JS using the Bun bundler and return built JS assets.
 * @param {Record<string, string>} entrypoints A mapping from chunk name to entrypoint script
 * @param {boolean} production true to build production-ready assets, false for development
 * @returns {Promise<Artifact[]>} A promise to return the built artifacts
 */
async function buildJs(
    entrypoints: Record<string, string>,
    production: boolean,
): Promise<Artifact[]> {
    const results = await build({
        entrypoints: Object.values(entrypoints),
        outdir: DIST_DIR,
        minify: production,
        target: "browser",
        format: "esm",
        splitting: false,
        sourcemap: production ? "none" : "external",
        plugins: [],
        naming: {
            entry: "[dir]/[name].[hash].[ext]",
            asset: "[name].[hash].[ext]",
            chunk: "[name].[hash].chunk.[ext]",
        },
        publicPath: STATIC_URL,
    });

    return results.outputs.map((artifact) => ({
        kind: artifact.kind,
        path: artifact.path,
        hash: artifact.hash,
    }));
}

/**
 * Build CSS using the Tailwind CLI and return built CSS assets.
 * @param {Record<string, string>} entrypoints A mapping from chunk name to entrypoint script
 * @param {boolean} production true to build production-ready assets, false for development
 * @returns {Promise<Artifact[]>} Information about each built CSS file
 */
async function buildCss(
    entrypoints: Record<string, string>,
    production: boolean,
): Promise<Artifact[]> {
    const tailwindArtifacts: Artifact[] = [];

    if (!existsSync(DIST_DIR)) {
        mkdirSync(DIST_DIR);
    }

    if (!existsSync(TAILWIND_EXECUTABLE)) {
        throw new Error("Tailwind is not installed!");
    }

    // Execute tailwindcss/cli for each entrypoint
    await Promise.all(
        Object.entries(entrypoints).map(async ([name, inputPath]) => {
            const args = [
                "-i", inputPath,
                "-o", "-", // Output to stdout
            ];

            if (production) {
                args.push("--minify");
            }

            const result = Bun.spawn([TAILWIND_EXECUTABLE, ...args], {
                stdout: "pipe",
                stderr: "pipe",
            });

            const cssContent = await new Response(result.stdout).text();
            const stderr = await new Response(result.stderr).text();

            if (stderr) {
                console.info(stderr);
            }

            const hash = createHash("md5").update(cssContent).digest("hex").slice(0, 8);
            const filename = `${name}.${hash}.css`;
            const outputDir = path.join(DIST_DIR, name);
            const outputPath = path.join(outputDir, filename);

            if (!existsSync(outputDir)) {
                mkdirSync(outputDir);
            }

            writeFileSync(outputPath, cssContent, "utf8");

            tailwindArtifacts.push({
                kind: "entry-point",
                path: outputPath,
                hash: hash,
            });
        })
    );

    return tailwindArtifacts;
}

/**
 * Create an object containing assets and chunks that matches the format of the
 * webpack-bundle-tracker file.
 * @param {Artifact[]} artifacts Built CSS and JS artifacts
 * @returns {WebpackStats} An object that matches the format of the webpack stats file.
 */
function generateWebpackStats(artifacts: Artifact[]): WebpackStats {
    const webpackStats: WebpackStats = {
        status: "done",
        assets: {},
        chunks: {},
    };

    for (const artifact of artifacts) {
        if (artifact.kind !== "entry-point" && artifact.kind !== "asset") {
            continue;
        }

        const absPath = artifact.path.replace(/\\/g, "/");
        const relPath = path.relative("./dist/", absPath).replace(/\\/g, "/");
        const filename = path.basename(artifact.path);
        const pubPath = (STATIC_URL + relPath).replace(/\\/g, "/");
        const chunkName = filename.split(".")[0];

        if (!(chunkName in webpackStats.chunks)) {
            webpackStats.chunks[chunkName] = [];
        }

        webpackStats.chunks[chunkName].push(relPath);

        webpackStats.assets[relPath] = {
            name: filename,
            path: relPath,
            publicPath: pubPath,
        };
    }

    return webpackStats;
}


/**
 * Run complete build.
 * @param {BuildOptions} options Options that control the build
 */
async function runBuild(options: BuildOptions | null) {
    const mode = options?.production ? "production" : "development";

    console.info(`Running build in ${mode} mode\n`);

    if (options?.clean && existsSync(DIST_DIR)) {
        console.info(`Removing ${DIST_DIR} because of --clean`);
        rmSync(DIST_DIR, { recursive: true, force: true });
        console.info("Removed dist directory\n");
    }

    console.info(`Building ${Object.keys(JS_ENTRYPOINTS).length} JS entrypoints`);
    const jsArtifacts = await buildJs(JS_ENTRYPOINTS, options?.production ?? false);
    console.info("JS Build Done.\n");

    console.info(`Building ${Object.keys(CSS_ENTRYPOINTS).length} CSS entrypoints`);
    const cssArtifacts = await buildCss(CSS_ENTRYPOINTS, options?.production ?? false);
    console.info("CSS Build Done.\n");

    const stats = generateWebpackStats([
        ...jsArtifacts,
        ...cssArtifacts,
    ]);

    writeFileSync(STATS_FILE, JSON.stringify(stats, null, 2), "utf8");
    console.info(`Stats written to ${STATS_FILE}`);
}

/**
 * Start watching for file changes and rebuild on changes.
 * @param {BuildOptions} options Options that control the build
 */
async function startWatchMode(options: BuildOptions) {
    await runBuild(options);

    console.info(`\nWatching for changes in ${WATCH_DIR}...`);

    let debounceTimer: ReturnType<typeof setTimeout> | null = null;
    let isBuilding = false;

    const triggerBuild = async (fileChanged: string) => {
        if (isBuilding) {
            return;
        }

        isBuilding = true;

        console.info(`\nFile changed: ${fileChanged}`);
        console.info("💫 Rebuilding...\n");

        try {
            await runBuild({ ...options, clean: false });
        } catch (error) {
            console.error("Build failed:", error);
        }

        isBuilding = false;
    };

    watch(WATCH_DIR, { recursive: true }, (_event, filename) => {
        if (null === filename) {
            return;
        }

        const extension = path.extname(filename).toLowerCase();

        if (-1 === WATCHED_ASSETS.indexOf(extension)) {
            return;
        }

        if (debounceTimer) {
            clearTimeout(debounceTimer);
        }

        debounceTimer = setTimeout(() => { triggerBuild(filename); }, DEBOUNCE_MS);
    });

    process.on("SIGINT", () => {
        console.info("\nStopping watch mode.");
        process.exit(0);
    });
}

const installed = await ensureTailwindInstalled();

if (!installed) {
    console.error("Could not install Tailwind CLI, aborting.");
    process.exit(1);
}
else if (installed && values["only-tailwind"]) {
    // Exit early if only tailwind.
    console.info("Tailwind CLI is installed");
    process.exit(0);
}
else {
    const buildOptions: BuildOptions = {
        clean: values.clean ?? false,
        production: isProd,
    };

    if (values.watch ?? false) {
        await startWatchMode(buildOptions);
    } else {
        await runBuild(buildOptions);
    }
}
