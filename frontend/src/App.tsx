import { BrowserRouter, Route, Routes } from "react-router-dom";
import CreateDatasetPage from "./pages/CreateDatasetPage";
import DatasetsPage from "./pages/DatasetsPage";
import GeneratePage from "./pages/GeneratePage";
import RunSchedulePage from "./pages/RunSchedulePage";
import RunsPage from "./pages/RunsPage";
import Navbar from "./components/Navbar";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <a className="skip-link" href="#main-content">
          Skip to Content
        </a>
        <Navbar />

        <main className="app-main" id="main-content">
          <Routes>
            <Route path="/" element={<GeneratePage />} />
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/datasets/new" element={<CreateDatasetPage />} />
            <Route path="/runs" element={<RunsPage />} />
            <Route path="/runs/:runId/schedule" element={<RunSchedulePage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
