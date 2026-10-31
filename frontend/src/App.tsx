import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ChatPage from "./pages/ChatPage";
import KnowledgeBasePage from "./pages/KnowledgeBasePage";
import KnowledgeBasesPage from "./pages/KnowledgeBasesPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:id" element={<ChatPage />} />
        <Route path="/kb" element={<KnowledgeBasesPage />} />
        <Route path="/kb/:id" element={<KnowledgeBasePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Route>
    </Routes>
  );
}
