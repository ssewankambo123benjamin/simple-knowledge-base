import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Cloudscape global styles (import ONCE here)
import '@cloudscape-design/global-styles/index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
