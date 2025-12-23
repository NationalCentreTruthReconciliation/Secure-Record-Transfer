/**
 * Build Javascript assets with Bun and CSS assets with the Tailwind CLI.
 *
 * Activate watched mode with --watch
 * Clean dist/ dir before building with --clean
 *
 * Generates JSON stats to mimic webpack-bundle-tracker. See: https://www.npmjs.com/package/webpack-bundle-tracker
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, rmSync, watch, writeFileSync } from "node:fs";
import path from "node:path";
import { build } from "bun";

const args = Bun.argv;
const shouldClean = args.includes("--clean");
const shouldWatch = args.includes("--watch");
const isProd = process.env.NODE_ENV === "production";

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

            const result = Bun.spawn(["bun", "run", "tailwindcss", ...args], {
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

const buildOptions: BuildOptions = {
    clean: shouldClean,
    production: isProd,
};

if (shouldWatch) {
    await startWatchMode(buildOptions);
} else {
    await runBuild(buildOptions);
}
