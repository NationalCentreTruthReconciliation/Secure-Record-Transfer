const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const glob = require('glob');

module.exports = {
    mode: 'production',
    entry: {
        base: [
            './bagitobjecttransfer/recordtransfer/static/recordtransfer/js/base/index.js',
            ...glob.sync('./bagitobjecttransfer/recordtransfer/static/recordtransfer/css/base/*.css')
                .map(file => './' + path.relative(__dirname, file))
        ],
    },
    output: {
        filename: '[name].bundle.js', // Output JS files
        path: path.resolve(__dirname, 'dist')
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
    ]
}