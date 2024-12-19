import globals from "globals";
import pluginJs from "@eslint/js";


/** @type {import('eslint').Linter.Config[]} */
export default [
  { languageOptions: { globals: globals.browser } },
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