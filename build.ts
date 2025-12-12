/**
 * Build static assets with Bun and generate JSON stats to mimic webpack-bundle-tracker.
 *
 * See: https://www.npmjs.com/package/webpack-bundle-tracker
 */
import { writeFileSync } from "node:fs";
import path from "node:path";
import plugin from "bun-plugin-tailwind";
import sharp from "sharp";

const ENTRYPOINTS = [
    path.join(import.meta.dir, "app/frontend/admin/admin.ts"),
    path.join(import.meta.dir, "app/frontend/app/app.ts"),
];

const DIST_DIR = path.join(import.meta.dir, "dist");
const IMG_DIR = path.join(import.meta.dir, "app/recordtransfer/static/recordtransfer/img");

const STATIC_URL = "/static/";
const STATS_FILE = path.join(import.meta.dir, "dist/webpack-stats.json");
const isProd = process.env.BUN_ENV === "production";

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
 * Create an object containing assets and chunks that matches the format of the
 * webpack-bundle-tracker file.
 * @param {Bun.BuildOutput} output The output from the Bun build step
 * @returns {WebpackStats} An object that matches the format of the webpack stats file.
 */
function generateWebpackStats(output: Bun.BuildOutput): WebpackStats {
    const webpackStats: WebpackStats = {
        status: "done",
        assets: {},
        chunks: {},
    };

    for (const artifact of output.outputs) {
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

const mode = isProd ? "production" : "development";

console.info(`Running build in ${mode} mode`);

await Bun.build({
    entrypoints: ENTRYPOINTS,
    outdir: DIST_DIR,
    minify: isProd,
    target: "browser",
    format: "esm",
    splitting: false,
    sourcemap: isProd ? "none" : "external",
    plugins: [plugin],
    naming: {
        entry: "[dir]/[name].[hash].[ext]",
        asset: "[name].[hash].[ext]",
        chunk: "[name].[hash].chunk.[ext]",
    },
    publicPath: STATIC_URL,
}).then((build) => {
    const stats = generateWebpackStats(build);
    writeFileSync(STATS_FILE, JSON.stringify(stats, null, 2), "utf8");
    console.info(`Stats written to ${STATS_FILE}`);
}).then(async () => {
    const glob = new Bun.Glob("*.{jpg,jpeg,png}");
    const files = await Array.fromAsync(glob.scan({ cwd: IMG_DIR }));

    await Promise.all(
        files.map(async (filename) => {
            const inputPath = path.join(IMG_DIR, filename);
            const base = path.basename(filename, path.extname(filename));
            const webpName = `${base}.webp`;
            const outputPath = path.join(DIST_DIR, webpName);

            const inputBuffer = await Bun.file(inputPath).arrayBuffer();
            const buffer = await sharp(Buffer.from(inputBuffer))
                .webp({ quality: 80 })
                .toBuffer();

            writeFileSync(outputPath, buffer);
        })
    );

    console.info(`Converted ${files.length} images to WebP in ${DIST_DIR}`);
});
