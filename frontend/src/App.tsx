import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";
import KnowledgeBasesPage from "./pages/KnowledgeBasesPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/kb" replace />} />
        <Route path="/kb" element={<KnowledgeBasesPage />} />
        <Route path="/kb/:id" element={<KnowledgeBasePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/kb" replace />} />
      </Route>
    </Routes>
  );
}
