import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Public demo: cloudflared trycloudflare tünellerinden gelen Host başlıklarını
  // kabul et (dev-only; production build nginx üzerinden sunulur).
  server: {
    host: true,
    allowedHosts: true,
  },
})
