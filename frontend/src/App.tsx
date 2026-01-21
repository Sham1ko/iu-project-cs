import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import DatasetsPage from "./pages/DatasetsPage";
import GeneratePage from "./pages/GeneratePage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <div className="brand">
            <span className="brand-mark">GA</span>
            <div>
              <div className="brand-title">Timetable Studio</div>
              <div className="brand-subtitle">FastAPI + GA runner</div>
            </div>
          </div>
          <nav className="nav">
            <NavLink to="/" end>
              Generate
            </NavLink>
            <NavLink to="/datasets">Datasets</NavLink>
          </nav>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<GeneratePage />} />
            <Route path="/datasets" element={<DatasetsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
