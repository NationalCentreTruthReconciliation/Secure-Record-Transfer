import pluginJs from "@eslint/js";
import stylisticJs from "@stylistic/eslint-plugin-js";
import importPlugin from "eslint-plugin-import";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";


/** @type {import('eslint').Linter.Config[]} */
export default [
    {
        ignores: [
            "{env,venv,.env,.venv}/**",
            "dist/",
            "node_modules/",
            "app/static/",
            "docs/",
        ],
    },
    {
        languageOptions: { globals: globals.browser },
        plugins: {
            "@stylistic/js": stylisticJs,
            "import": importPlugin,
            "jsdoc": jsdoc,
        },
        rules: {
            // Plugin rules
            "@stylistic/js/indent": ["error", 4],
            "@stylistic/js/max-len": ["error", { code: 99, tabWidth: 4, ignoreUrls: true }],
            "@stylistic/js/semi": ["error", "always"],
            "@stylistic/js/quotes": ["error", "double"],
            "import/order": ["error", {
                "alphabetize": { "order": "asc", "caseInsensitive": true }
            }],
            // ESLint extra rules
            "no-console": "warn",
            "eqeqeq": "error",
            "curly": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
    {
        files: ["webpack.config.js"],
        languageOptions: {
            globals: globals.node,
        },
    },
    // Docstring rules
    jsdoc.configs["flat/recommended"],
    // Recommended ESLint rules
    pluginJs.configs.recommended,
];