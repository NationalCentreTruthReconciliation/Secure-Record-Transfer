import js from "@eslint/js";
import stylistic from "@stylistic/eslint-plugin";
import { defineConfig, globalIgnores } from "eslint/config";
import importPlugin from "eslint-plugin-import";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
    globalIgnores(
        [
            "{env,venv,.env,.venv}/*",
            "dist/*",
            "app/static/*",
            "docs/*"
        ],
    ),
    {
        files: ["app/**/*.{js,ts}"],
        plugins: {
            "js": js,
            "@stylistic": stylistic,
            "jsdoc": jsdoc,
            "import": importPlugin,
        },
        extends: [
            "js/recommended"
        ],
        languageOptions: {
            globals: globals.browser
        },
        rules: {
            // Plugin rules
            "@stylistic/indent": ["error", 4],
            "@stylistic/max-len": ["error", { code: 99, tabWidth: 4, ignoreUrls: true }],
            "@stylistic/semi": ["error", "always"],
            "@stylistic/space-before-blocks": ["error", "always"],
            "@stylistic/quotes": ["error", "double"],
            "import/order": ["error", {
                "alphabetize": { "order": "asc", "caseInsensitive": true }
            }],
            // ESLint extra rules
            "no-console": ["warn", { "allow": ["error", "warn", "info"] }],
            "eqeqeq": "error",
            "curly": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
    {
        files: [
            "webpack.config.mjs",
            "eslint.config.mjs",
            "postcss.config.mjs",
        ],
        plugins: {
            "js": js,
            "@stylistic": stylistic,
            "jsdoc": jsdoc,
            "import": importPlugin,
        },
        extends: [
            "js/recommended"
        ],
        languageOptions: {
            globals: globals.node
        },
        rules: {
            // Plugin rules
            "@stylistic/indent": ["error", 4],
            "@stylistic/max-len": ["error", { code: 99, tabWidth: 4, ignoreUrls: true }],
            "@stylistic/semi": ["error", "always"],
            "@stylistic/space-before-blocks": ["error", "always"],
            "@stylistic/quotes": ["error", "double"],
            "import/order": ["error", {
                "alphabetize": { "order": "asc", "caseInsensitive": true }
            }],
            // ESLint extra rules
            "no-console": ["warn", { "allow": ["error", "warn", "info"] }],
            "eqeqeq": "error",
            "curly": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
    jsdoc.configs["flat/recommended"],
    js.configs.recommended,
    tseslint.configs.recommended,
]);
