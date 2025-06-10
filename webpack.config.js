const path = require("path");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const glob = require("glob");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const sharp = require("sharp");
const BundleTracker = require("webpack-bundle-tracker");


console.info("CURRENT MODE IN WEBPACK: ", process.env.WEBPACK_MODE);

class WebPConverterPlugin {
    constructor(options = {}) {
        this.quality = options.quality || 85;
    }

    apply(compiler) {
        compiler.hooks.thisCompilation.tap("WebPConverterPlugin", (compilation) => {
            compilation.hooks.processAssets.tapAsync(
                {
                    name: "WebPConverterPlugin",
                    stage: compiler.webpack.Compilation.PROCESS_ASSETS_STAGE_ADDITIONS,
                },
                (assets, callback) => {
                    const promises = [];

                    Object.keys(assets).forEach(filename => {
                        if (filename.match(/\.(jpe?g|png)$/i)) {
                            const asset = assets[filename];
                            const source = asset.source();
                            const webpFilename = filename.replace(/\.(jpe?g|png)$/i, ".webp");

                            const promise = sharp(source)
                                .webp({ quality: this.quality })
                                .toBuffer()
                                .then(buffer => {
                                    // Emit the WebP version
                                    compilation.emitAsset(webpFilename, {
                                        source: () => buffer,
                                        size: () => buffer.length
                                    });
                                    // Remove the original asset
                                    compilation.deleteAsset(filename);
                                });

                            promises.push(promise);
                        }
                    });

                    Promise.all(promises).then(() => callback());
                }
            );
        });
    }
}


module.exports = {
    mode: process.env.WEBPACK_MODE === "production" ? "production" : "development",
    devtool: process.env.WEBPACK_MODE === "production" ? false : "eval-source-map",
    watchOptions: {
        aggregateTimeout: 500,
        poll: 1000,
        ignored: [
            "**/node_modules/**",
            "**/dist/**",
        ],
    },
    entry: {
        images: [
            ...glob.sync("./app/recordtransfer/static/recordtransfer/img/*.{jpg,jpeg,png,webp}") // eslint-disable-line
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        main: "./app/recordtransfer/static/recordtransfer/js/index.js",
        // The submission detail page has its own styling (TODO: FIX!)
        submission_detail: [
            ...glob.sync(
                "./app/recordtransfer/static/" +
                "recordtransfer/css/submission_detail/*.css")
                .map(file => "./" + path.relative(__dirname, file)),
        ],

        // Admin Site static assets
        admin_metadata: [
            ...glob.sync("./app/caais/static/caais/css/base/*.css")
                .map(file => "./" + path.relative(__dirname, file)),
            ...glob.sync("./app/caais/static/caais/js/admin/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        admin_uploadedfile: [
            ...glob.sync("./app/recordtransfer/static/" +
                "recordtransfer/js/admin/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        admin_job: [
            ...glob.sync("./app/recordtransfer/static/" +
                "recordtransfer/css/admin/job.css")
                .map(file => "./" + path.relative(__dirname, file)),
        ]
    },
    output: {
        path: path.join(__dirname, "../build"),
        filename: "js/[name].js",
        publicPath: "/static/",
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, "css-loader", "postcss-loader"] // Extract CSS
            },
            {
                test: /\.(jpe?g|png|webp)$/i,
                type: "asset/resource",
                generator: {
                    filename: "[name][ext]"
                }
            },
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "css/app-[contenthash].css",
        }),
        new WebPConverterPlugin({
            quality: 80
        }),
        new BundleTracker({filename: "./webpack-stats.json"}),

    ],
    optimization: {
        minimizer: [
            "...", // This keeps the default JavaScript minifier
            new CssMinimizerPlugin(), // Add this line to minify CSS
        ],

        splitChunks: {
            cacheGroups: {
                vendor: {
                    test: /[\\/]node_modules[\\/]/,
                    name: "vendors",
                    chunks: "all"
                }
            }
        },
    }
};

