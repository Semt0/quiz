import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// 本地开发 base 为 '/'；CI 通过 BASE_URL=/quiz/ 指定子路径。
const base = process.env.BASE_URL || '/';

export default defineConfig({
  base,
  plugins: [svelte()],
  build: {
    outDir: 'dist',
    target: 'es2020',
    cssCodeSplit: true,
    assetsInlineLimit: 2048,
  },
  server: {
    port: 5173,
    open: true,
  },
});
