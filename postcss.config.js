module.exports = {
    plugins: [
        // eslint-disable-next-line global-require
        require('autoprefixer'),
        [
            'cssnano',
            {
                preset: [
                    'default',
                    {
                        discardComments: { removeAll: true },
                        normalizeWhitespace: true,
                        mergeLonghand: true,
                        mergeRules: true,
                        discardDuplicates: true,
                        discardEmpty: true,
                        minifySelectors: true,
                        colormin: true,
                        convertValues: true,
                    },
                ],
            },
        ],
    ],
};
