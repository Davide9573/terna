import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ConfigPage from './pages/ConfigPage'
import ResultsPage from './pages/ResultsPage'
import SimulationPage from './pages/SimulationPage'
import CostAnalysisPage from './pages/CostAnalysisPage'
import ConclusionsPage from './pages/ConclusionsPage'
import { ScenarioProvider } from './contexts/ScenarioContext'

export default function App() {
  return (
    <ScenarioProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/simulation" element={<SimulationPage />} />
          <Route path="/cost-analysis" element={<CostAnalysisPage />} />
          <Route path="/conclusions" element={<ConclusionsPage />} />
        </Routes>
      </BrowserRouter>
    </ScenarioProvider>
  )
}