/* eslint-disable radix */
const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const StyleLintPlugin = require('stylelint-webpack-plugin');
const ESLintPlugin = require('eslint-webpack-plugin');
const BrowserSyncPlugin = require('browser-sync-webpack-plugin');
const WebpackNotifierPlugin = require('webpack-notifier');
const SVGSpritemapPlugin = require('svg-spritemap-webpack-plugin');
const sassEmbedded = require('sass-embedded');
const ImageMinimizerPlugin = require('image-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');

// Webpack clean dist
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

const django_ip = process.env.DJANGO_IP || '127.0.0.1';
const django_port = parseInt(process.env.DJANGO_PORT || 8000);
const browsersync_port = parseInt(process.env.BROWSERSYNC_PORT || django_port + 1);
const browsersyncui_port = browsersync_port + 1;

const config = {
    entry: {
        app: ['./static/src/js/app.js'],
        sentry_config: ['./static/src/js/sentry_config.js'],
        styles: ['./static/src/scss/styles.scss'],
    },
    output: {
        path: path.resolve('./static/dist/'),
        filename: 'js/[name].[contenthash:8].js',
        assetModuleFilename: 'assets/[hash][ext][query]',
    },
    sharedPlugins: {
        svgSprite: new SVGSpritemapPlugin('./static/src/sprite/*.svg', {
            output: {
                filename: './svg/sprite.svg',
            },
            sprite: {
                prefix: false,
            },
        }),
        miniCssExtract: new MiniCssExtractPlugin({
            filename: 'css/[name].[contenthash:8].css',
            chunkFilename: 'css/[id].[contenthash:8].css',
            ignoreOrder: true,
        }),
        manifest: new WebpackManifestPlugin({
            fileName: 'manifest.json',
            publicPath: '/static/dist/',
        }),
    },
};

module.exports = [
    // Development webpack config
    {
        name: 'development',
        entry: config.entry,
        output: config.output,

        plugins: [
            // Dist clean
            new CleanWebpackPlugin({
                cleanStaleWebpackAssets: false,
            }),

            // Shared plugins
            config.sharedPlugins.svgSprite,
            config.sharedPlugins.manifest,
            config.sharedPlugins.miniCssExtract,

            new StyleLintPlugin({
                files: 'static/src/scss',
                failOnError: false,
            }),

            // eslint plugin
            new ESLintPlugin(),

            // BrowserSync
            new BrowserSyncPlugin(
                {
                    host: django_ip,
                    port: browsersync_port,
                    injectCss: true,
                    ghostMode: false,
                    logLevel: 'silent',
                    files: ['./static/dist/css/*.css', './static/dist/js/*.js'],
                    ignore: ['./static/dist/js/styles.js'],
                    ui: {
                        port: browsersyncui_port,
                    },
                },
                {
                    reload: false,
                },
            ),

            new WebpackNotifierPlugin(),
        ],

        module: {
            rules: [
                {
                    test: /\.(png|jpg|woff|woff2|eot|ttf|svg|otf)$/,
                    exclude: /node_modules/,
                    type: 'asset/resource',
                },
                {
                    test: /\.js$/,
                    exclude: /node_modules/,
                    use: {
                        loader: 'babel-loader',
                        options: {
                            presets: [
                                [
                                    '@babel/preset-env',
                                    {
                                        useBuiltIns: 'usage',
                                        corejs: 3,
                                    },
                                ],
                            ],
                        },
                    },
                },
                {
                    test: /\.scss$/,
                    exclude: /node_modules/,
                    use: [
                        MiniCssExtractPlugin.loader,
                        {
                            loader: 'css-loader',
                            options: { sourceMap: true },
                        },
                        {
                            loader: 'postcss-loader',
                            options: { sourceMap: true },
                        },
                        {
                            loader: 'sass-loader',
                            options: {
                                api: 'modern',
                                sourceMap: true,
                                implementation: sassEmbedded,
                                sassOptions: {
                                    loadPaths: ['node_modules'],
                                },
                            },
                        },
                    ],
                },
                {
                    test: /\.css$/,
                    exclude: /node_modules/,
                    use: [
                        'style-loader',
                        {
                            loader: 'css-loader',
                            options: { sourceMap: true },
                        },
                    ],
                },
            ],
        },

        stats: {
            colors: true,
            version: true,
            timings: true,
            assets: true,
            chunks: false,
            source: true,
            errors: true,
            errorDetails: true,
            warnings: true,
            hash: false,
            modules: false,
            reasons: false,
            children: false,
            publicPath: false,
        },

        devtool: 'source-map',
    },

    // Production webpack config
    // Source maps are disabled to reduce filesize
    {
        name: 'production',
        entry: config.entry,
        output: config.output,

        plugins: [
            // Shared plugins
            config.sharedPlugins.svgSprite,
            config.sharedPlugins.manifest,
            config.sharedPlugins.miniCssExtract,

            new StyleLintPlugin({
                configFile: '.stylelintrc',
                context: '',
                files: '/static/src/scss/**/*.scss',
                syntax: 'scss',
                failOnError: false,
                quiet: false,
            }),

            new ImageMinimizerPlugin({
                minimizer: {
                    implementation: ImageMinimizerPlugin.sharpMinify,
                    options: {
                        encodeOptions: {
                            jpeg: { quality: 75 },
                            png: { quality: 90 },
                        },
                    },
                },
            }),
        ],

        optimization: {
            minimizer: [
                new TerserPlugin({
                    terserOptions: {
                        compress: {
                            drop_console: true,
                        },
                    },
                }),
            ],
            splitChunks: {
                cacheGroups: {
                    // Split vendor CSS
                    vendorStyles: {
                        name: 'vendor',
                        test: /[\\/]node_modules[\\/].*\.(css|scss)$/,
                        chunks: 'all',
                        enforce: true,
                    },
                    // Split your own styles by component/page
                    criticalStyles: {
                        name: 'critical',
                        test: /critical.*\.(css|scss)$/,
                        chunks: 'all',
                        priority: 30,
                    },
                },
            },
        },

        module: {
            rules: [
                {
                    test: /\.js$/,
                    exclude: /node_modules/,
                    use: {
                        loader: 'babel-loader',
                        options: {
                            presets: [
                                [
                                    '@babel/preset-env',
                                    {
                                        useBuiltIns: 'usage',
                                        corejs: 3,
                                    },
                                ],
                            ],
                        },
                    },
                },
                {
                    test: /\.(png|jpg|woff|woff2|eot|ttf|svg|otf)$/,
                    exclude: /node_modules/,
                    type: 'asset/resource',
                    parser: {
                        dataUrlCondition: {
                            maxSize: 4 * 1024, // Inline images smaller than 4KB
                        },
                    },
                },
                {
                    test: /\.scss$/,
                    use: [
                        MiniCssExtractPlugin.loader,
                        {
                            loader: 'css-loader',
                            options: {
                                importLoaders: 2,
                                sourceMap: false,
                            },
                        },
                        {
                            loader: 'postcss-loader',
                            options: { sourceMap: false },
                        },
                        {
                            loader: 'sass-loader',
                            options: {
                                api: 'modern',
                                sourceMap: false,
                                implementation: sassEmbedded,
                                sassOptions: {
                                    loadPaths: ['node_modules'],
                                    outputStyle: 'compressed',
                                },
                            },
                        },
                    ],
                },
            ],
        },

        devtool: false,
    },
];
