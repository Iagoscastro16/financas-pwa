import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import PrivateRoute from "./routes/PrivateRoute";
import Layout from "./components/Layout/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Transacoes from "./pages/Transacoes";
import Orcamentos from "./pages/Orcamentos";
import Metas from "./pages/Metas";

function PrivatePage({ children }) {
  return (
    <PrivateRoute>
      <Layout>{children}</Layout>
    </PrivateRoute>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <PrivatePage>
              <Dashboard />
            </PrivatePage>
          }
        />
        <Route
          path="/transacoes"
          element={
            <PrivatePage>
              <Transacoes />
            </PrivatePage>
          }
        />
        <Route
          path="/orcamentos"
          element={
            <PrivatePage>
              <Orcamentos />
            </PrivatePage>
          }
        />
        <Route
          path="/metas"
          element={
            <PrivatePage>
              <Metas />
            </PrivatePage>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}
