import eslint from "@eslint/js"
import tseslint from "typescript-eslint"

export default tseslint.config(eslint.configs.all, ...tseslint.configs.all, {
    rules: {
        camelcase: "off",
        "@typescript-eslint/naming-convention": "off",
        "sort-keys": "off",
        "@typescript-eslint/no-unsafe-argument": "off",
        "sort-imports": "off",
        "@typescript-eslint/prefer-enum-initializers": "off",
        "func-style": ["error", "declaration"],
        "one-var": ["error", "never"],
        "@typescript-eslint/no-shadow": "off",
        "no-magic-numbers": "off",
        "@typescript-eslint/no-magic-numbers": "off",
        "@typescript-eslint/prefer-readonly-parameter-types": "off",
        "no-undefined": "off",
        "no-ternary": "off",
        "@typescript-eslint/explicit-function-return-type": "off",
        "no-return-await": "off",
        "@typescript-eslint/return-await": ["error", "always"],
        "no-void": "off",
        "@typescript-eslint/explicit-module-boundary-types": "off",
        "@typescript-eslint/no-empty-interface": "off",
        "@typescript-eslint/parameter-properties": "off",
        "@typescript-eslint/max-params": "off",
        "default-case": "off",
        "@typescript-eslint/init-declarations": "off",
        "@typescript-eslint/consistent-return": "off",
        "require-atomic-updates": "off",
        "max-statements": "off"
    },
    languageOptions: {
        parserOptions: {
            EXPERIMENTAL_useProjectService: true
        }
    }
})
