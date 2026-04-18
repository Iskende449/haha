import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'

import App from './App'
import './index.css'
import { AuthProvider } from '@/hooks/AuthProvider'
import { initApiBaseUrl } from '@/services/api'

const queryClient = new QueryClient()

document.documentElement.classList.add('dark')

async function bootstrap() {
  await initApiBaseUrl()

  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </React.StrictMode>,
  )
}

bootstrap()
