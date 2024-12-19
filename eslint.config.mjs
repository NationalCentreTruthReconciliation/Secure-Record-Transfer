import pluginJs from "@eslint/js";
import stylisticJs from "@stylistic/eslint-plugin-js";
import importPlugin from "eslint-plugin-import";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";


/** @type {import('eslint').Linter.Config[]} */
export default [
    {
        languageOptions: { globals: globals.browser },
        plugins: {
            "@stylistic/js": stylisticJs,
            "import": importPlugin,
            "jsdoc": jsdoc,
        },
        rules: {
            "@stylistic/js/indent": ["error", 4],
            "@stylistic/js/max-len": ["error", { code: 99, tabWidth: 4, ignoreUrls: true }],
            "@stylistic/js/semi": ["error", "always"],
            "@stylistic/js/quotes": ["error", "double"],
            "import/order": ["error", {
                "alphabetize": { "order": "asc", "caseInsensitive": true }
            }],
        }
    },
    jsdoc.configs["flat/recommended"],
    pluginJs.configs.recommended,
    {
        rules: {
            "no-console": "warn",
            "eqeqeq": "error",
            "curly": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
];