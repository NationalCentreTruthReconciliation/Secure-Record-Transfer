import globals from "globals";
import js from "@eslint/js";

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    languageOptions: { globals: globals.browser },
    extends: ["eslint:recommended"],
    rules: {
      "no-console": "warn",
      "eqeqeq": "error",
      "curly": "error",
      "sort-imports": "error",
    },
  },
  js.configs.recommended,
];