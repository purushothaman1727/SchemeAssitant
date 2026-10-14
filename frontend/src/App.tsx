import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Chat from "./pages/Chat";
import Home from "./pages/Home";
import Admin from "./pages/Admin";
import Privacy from "./pages/Privacy";
import Profile from "./pages/Profile";
import Results from "./pages/Results";
import SchemeDetail from "./pages/SchemeDetail";
import Schemes from "./pages/Schemes";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="profile" element={<Profile />} />
        <Route path="profile/disability" element={<Profile />} />
        <Route path="results" element={<Results />} />
        <Route path="schemes" element={<Schemes />} />
        <Route path="schemes/:id" element={<SchemeDetail />} />
        <Route path="chat" element={<Chat />} />
        <Route path="admin" element={<Admin />} />
        <Route path="privacy" element={<Privacy />} />
      </Route>
    </Routes>
  );
}
