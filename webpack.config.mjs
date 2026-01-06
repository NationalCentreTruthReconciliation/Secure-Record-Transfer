import path, { dirname } from "path";
import { fileURLToPath } from "url";
import CssMinimizerPlugin from "css-minimizer-webpack-plugin";
import MiniCssExtractPlugin from "mini-css-extract-plugin";
import BundleTracker from "webpack-bundle-tracker";

const mode = process.env.WEBPACK_MODE || "production"; // Default if not passed

console.info("CURRENT MODE IN WEBPACK: ", mode);

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);


export default {
    mode: mode,
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
        main: "./app/frontend/main/index.ts",
        admin: "./app/frontend/admin/index.ts",
    },
    output: {
        filename: "js/[name].[chunkhash:8].js",
        chunkFilename: "js/[name].[chunkhash:8].chunk.js",
        path: path.resolve(__dirname, "dist/"),
        publicPath: "/static/",
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, "css-loader", "postcss-loader"] // Extract CSS
            },
            {
                test: /\.ico$/i,
                type: "asset/resource",
                generator: {
                    filename: "[name][ext]" // Match your template path
                }
            },
            {
                test: /\.ts$/,
                use: "ts-loader",
                exclude: /node_modules/,
            },
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: "css/[name].[contenthash:8].css",
        }),
        new BundleTracker({
            path: path.resolve(__dirname, "dist"),
            filename: "webpack-stats.json"
        })
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

