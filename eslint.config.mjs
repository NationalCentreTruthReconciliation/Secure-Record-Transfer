import eslint from "@eslint/js";
import tseslint from "typescript-eslint";
import stylisticJs from "@stylistic/eslint-plugin";
import importPlugin from "eslint-plugin-import";
import jsdoc from "eslint-plugin-jsdoc";
import globals from "globals";

export default [
    {
        ignores: [
            "{env,venv,.env,.venv}/**",
            "dist/**",
            "node_modules/**",
            "docs/**",
            "app/static/**",
        ],
    },
    {
        files: ["app/**/*.{js,ts}"],
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
            "no-console": ["warn", { "allow": ["error", "warn", "info"] }],
            "eqeqeq": "error",
            "curly": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
    {
        files: [
            "build.ts",
            "scripts/*.ts",
        ],
        languageOptions: { globals: { ...globals.nodeBuiltin, Bun: "readonly" } },
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
            "no-console": ["warn", { "allow": ["error", "warn", "info"] }],
            "eqeqeq": "error",
            "curly": "error",
            "prefer-const": "error",
            "no-duplicate-imports": "error",
        }
    },
    // Docstring rules
    { ...jsdoc.configs["flat/recommended"], files: ["app/**/*.{js,ts}", "build.ts", "scripts/*.ts"] },
    // Recommended ESLint rules
    { ...eslint.configs.recommended, files: ["app/**/*.{js,ts}", "build.ts", "scripts/*.ts"] },
    ...tseslint.configs.recommended.map(config => ({ ...config, files: ["app/**/*.{js,ts}", "build.ts", "scripts/*.ts"] })),
];
