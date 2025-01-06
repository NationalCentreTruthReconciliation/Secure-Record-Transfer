const path = require("path");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const glob = require("glob");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

console.log("CURRENT MODE IN WEBPACK: ", process.env.WEBPACK_MODE);

module.exports = {
    mode: process.env.WEBPACK_MODE === "production" ? "production" : "development",
    devtool: false,
    watchOptions: {
        aggregateTimeout: 500,
        poll: 1000,
        ignored: /node_modules/,
    },
    entry: {
        base: [
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/base/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
            ...glob.sync("./bagitobjecttransfer/recordtransfer/static/" + 
                "recordtransfer/css/base/*.css").map(file => "./" + path.relative(__dirname, file))
        ],
        transferform: [
            ...glob.sync(
                "./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/transferform/*.js")
                .map(file => "./" + path.relative(__dirname, file)),
        ],
        profile: [
            ...glob.sync(
                "./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/profile/*.js")
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
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "[name].css" // Output CSS file
        })
    ],
    optimization: {
        minimizer: [
            "...", // This keeps the default JavaScript minifier
            new CssMinimizerPlugin(), // Add this line to minify CSS
        ],
    }
};
