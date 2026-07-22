import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(
    mode,
    process.cwd(),
    '',
  )

  const backendProxyTarget =
    env.VITE_BACKEND_PROXY_TARGET
    || 'http://127.0.0.1:8000'

  return {
    plugins: [vue()],

    resolve: {
      alias: {
        '@': fileURLToPath(
          new URL('./src', import.meta.url),
        ),
      },
    },

    server: {
      proxy: {
        '/api': {
          target: backendProxyTarget,
          changeOrigin: true,
          rewrite: (path) =>
            path.replace(/^\/api/, ''),
        },
      },
    },
  }
})