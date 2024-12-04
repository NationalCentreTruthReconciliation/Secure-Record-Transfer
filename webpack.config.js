const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const glob = require('glob');
const dotenv = require('dotenv');

dotenv.config();

console.log("CURRENT MODE IN WBEPACK: ", process.env.MODE)

module.exports = {
    mode: process.env.MODE === 'production' ? 'production' : 'development',
    devtool: false,
    entry: {
        base: [
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/base/*.js')
                .map(file => './' + path.relative(__dirname, file)),
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/css/base/*.css')
                .map(file => './' + path.relative(__dirname, file))
        ],
        transferform: [
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/transferform/*.js')
                .map(file => './' + path.relative(__dirname, file)),
        ],
        profile: [
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/profile/*.js')
                .map(file => './' + path.relative(__dirname, file)),
        ],
        submissiondetail: [
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/css/submission_detail/*.css')
                .map(file => './' + path.relative(__dirname, file)),
        ],
        submissiongroup: [
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/js/submission_group/*.js')
                .map(file => './' + path.relative(__dirname, file)),
        ]
    },
    output: {
        filename: '[name].bundle.js', // Output JS files
        path: path.resolve(__dirname, 'static/')
    },
    module: {
        rules: [
            {
                test: /\.css$/,
                use: [MiniCssExtractPlugin.loader, 'css-loader'] // Extract CSS
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: '[name].css' // Output CSS file
        })
    ],
    optimization: {
        minimizer: [
            '...', // This keeps the default JavaScript minifier
            new CssMinimizerPlugin(), // Add this line to minify CSS
        ],
    }
}