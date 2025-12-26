import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { LabelsProvider } from './context/LabelsContext.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <LabelsProvider>
    <App />
    </LabelsProvider>
  </StrictMode>,
)
