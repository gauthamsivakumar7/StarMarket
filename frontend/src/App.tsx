import { Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AdminRoute } from './components/layout/AdminRoute'
import { AppShell } from './components/layout/AppShell'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { AssetsListPage } from './pages/AssetsListPage'
import { AssetDetailPage } from './pages/AssetDetailPage'
import { PortfolioPage } from './pages/PortfolioPage'
import { StrategiesListPage } from './pages/StrategiesListPage'
import { StrategyCreatePage } from './pages/StrategyCreatePage'
import { StrategyDetailPage } from './pages/StrategyDetailPage'
import { AdminPage } from './pages/AdminPage'
import { NotFoundPage } from './pages/NotFoundPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/assets" element={<AssetsListPage />} />
          <Route path="/assets/:assetId" element={<AssetDetailPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/strategies" element={<StrategiesListPage />} />
          <Route path="/strategies/new" element={<StrategyCreatePage />} />
          <Route path="/strategies/:strategyId" element={<StrategyDetailPage />} />
          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
