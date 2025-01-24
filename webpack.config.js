const path = require("path");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const glob = require("glob");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const sharp = require("sharp");

console.log("CURRENT MODE IN WEBPACK: ", process.env.WEBPACK_MODE);

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
    devtool: false,
    watchOptions: {
        aggregateTimeout: 500,
        poll: 1000,
        ignored: /node_modules/,
    },
    entry: {
        images: [
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/recordtransfer/img/*.{jpg,jpeg,png,webp}") // eslint-disable-line
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        base: [
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/base/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/" +
                "recordtransfer/css/base/*.css").map(file => "./" + path.relative(__dirname, file))
        ],
        transferform: [
            "./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/transferform/index.js",
        ],
        profile: [
            ...glob.sync(
                "./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/profile/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
            ...glob.sync(
                "./bagitobjecttransfer/recordtransfer/static/recordtransfer/css/profile/*.css")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        submissiondetail: [
            ...glob.sync(
                "./bagitobjecttransfer/recordtransfer/static/" +
                "recordtransfer/css/submission_detail/*.css")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        submissiongroup: [
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/" +
                "recordtransfer/js/submission_group/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        // Admin Site static assets
        admin_metadata: [
            ...glob.sync("./bagitobjecttransfer/caais/static/caais/css/base/*.css")
                .map(file => "./" + path.relative(__dirname, file)),
            ...glob.sync("./bagitobjecttransfer/caais/static/caais/js/admin/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        admin_uploadedfile: [
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/" +
                "recordtransfer/js/admin/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
        ]
    },
    output: {
        filename: "[name].bundle.js", // Output JS files
        path: path.resolve(__dirname, "dist/")
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, "css-loader"] // Extract CSS
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
            filename: "[name].css" // Output CSS file
        }),
        new WebPConverterPlugin({
            quality: 80
        }),
    ],
    optimization: {
        minimizer: [
            "...", // This keeps the default JavaScript minifier
            new CssMinimizerPlugin(), // Add this line to minify CSS
        ],
    }
};
