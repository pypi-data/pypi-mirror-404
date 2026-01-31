import commonjs from "@rollup/plugin-commonjs"
import resolve from "@rollup/plugin-node-resolve"
import replace from "@rollup/plugin-replace"
import typescript from "@rollup/plugin-typescript"
import postcss from "rollup-plugin-postcss"

export default {
  input: "src/index.tsx",
  // Bundle React instead of externalizing it to avoid CDN timing issues
  output: {
    file: "build/bundle.js",
    format: "iife",
    name: "streamlitEffects",
    sourcemap: true,
  },
  plugins: [
    replace({
      "process.env.NODE_ENV": JSON.stringify("production"),
      preventAssignment: true,
    }),
    resolve({
      browser: true,
      extensions: [".js", ".jsx", ".ts", ".tsx"],
    }),
    commonjs({
      include: /node_modules/,
    }),
    typescript({
      tsconfig: "./tsconfig.json",
      outputToFilesystem: true,
    }),
    postcss({
      extract: false,
      modules: false,
      use: ["sass"],
    }),
  ],
}
