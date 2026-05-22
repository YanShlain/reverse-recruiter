import { Link, Route, Routes } from "react-router-dom";
import { PipelinePage } from "./pages/PipelinePage";
import { SearchPage } from "./pages/SearchPage";

export function App() {
  return (
    <div className="app">
      <header>
        <strong>ReverseRecruiter</strong>
        <nav>
          <Link to="/">Search</Link>
          <Link to="/pipeline?filter=in_progress">Pipeline</Link>
          <Link to="/pipeline?filter=in_progress">Review queue</Link>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
      </Routes>
    </div>
  );
}
