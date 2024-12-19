import pluginJs from "@eslint/js";
import stylisticJs from "@stylistic/eslint-plugin-js";
import importPlugin from "eslint-plugin-import";
import globals from "globals";


/** @type {import('eslint').Linter.Config[]} */
export default [
    {
        languageOptions: { globals: globals.browser },
        plugins: {
            "@stylistic/js": stylisticJs,
            "import": importPlugin,
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