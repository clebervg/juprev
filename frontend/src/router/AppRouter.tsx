import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { Login } from "@/pages/Login";
import { Dashboard } from "@/pages/Dashboard";
import { ClientesPage } from "@/pages/Clientes";
import { ClienteForm } from "@/pages/Clientes/ClienteForm";
import { CNISPage } from "@/pages/CNIS";
import { CNISForm } from "@/pages/CNIS/CNISForm";
import { CNISDetalhes } from "@/pages/CNIS/CNISDetalhes";
import { CalculoRMIForm } from "@/pages/CNIS/CalculoRMIForm";
import { SimulacaoPage } from "@/pages/CNIS/SimulacaoPage";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clientes" element={<ClientesPage />} />
            <Route path="/clientes/novo" element={<ClienteForm />} />
            <Route path="/clientes/:id" element={<ClienteForm />} />
            <Route path="/cnis" element={<CNISPage />} />
            <Route path="/cnis/novo" element={<CNISForm />} />
            <Route path="/cnis/:cnisId" element={<CNISDetalhes />} />
            <Route path="/cnis/:cnisId/calcular" element={<CalculoRMIForm />} />
            <Route path="/cnis/:cnisId/simular" element={<SimulacaoPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
