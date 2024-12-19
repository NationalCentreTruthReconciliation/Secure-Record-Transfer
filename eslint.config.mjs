import globals from "globals";
import pluginJs from "@eslint/js";
import stylisticJs from '@stylistic/eslint-plugin-js'


/** @type {import('eslint').Linter.Config[]} */
export default [
    {
        languageOptions: { globals: globals.browser },
        plugins: {
            "@stylistic/js": stylisticJs
        },
        rules: {
            "@stylistic/js/indent": ["error", 4],
            "@stylistic/js/max-len": ["error", { code: 99, tabWidth: 4, ignoreUrls: true }],
            "@stylistic/js/semi": ["error", "always"],
            "@stylistic/js/quotes": ["error", "double"],
        }
    },
    pluginJs.configs.recommended,
    {
        rules: {
            "no-console": "warn",
            "eqeqeq": "error",
            "curly": "error",
            "sort-imports": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
];