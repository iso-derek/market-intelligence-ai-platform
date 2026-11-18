import { NavLink, Route, Routes } from "react-router-dom";
import News from "./pages/News";
import Watchlist from "./pages/Watchlist";
import Markets from "./pages/Markets";
import Filings from "./pages/Filings";
import Research from "./pages/Research";
import Evidence from "./pages/Evidence";
import Companies from "./pages/Companies";

const SECTIONS = [
  { to: "/", label: "News" },
  { to: "/watchlist", label: "Watchlist" },
  { to: "/markets", label: "Markets & macro" },
  { to: "/filings", label: "Filings" },
  { to: "/companies", label: "Company accounts" },
  { to: "/research", label: "Research desk" },
  { to: "/evidence", label: "Evidence & operations" },
];

export default function App() {
  const today = new Date().toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  return (
    <>
      <header className="masthead">
        <div className="masthead-top">
          <NavLink to="/" className="wordmark"><span className="wordmark-dot" aria-hidden />Market Signal</NavLink>
          <div className="dateline">{today}<br />Source-linked market research · educational fixtures</div>
        </div>
        <nav className="sections" aria-label="Sections">
          {SECTIONS.map((section) => <NavLink key={section.to} to={section.to} end={section.to === "/"}>{section.label}</NavLink>)}
        </nav>
      </header>
      <main className="wrap">
        <Routes>
          <Route index element={<News />} />
          <Route path="watchlist" element={<Watchlist />} />
          <Route path="markets" element={<Markets />} />
          <Route path="filings" element={<Filings />} />
          <Route path="companies" element={<Companies />} />
          <Route path="research" element={<Research />} />
          <Route path="evidence" element={<Evidence />} />
        </Routes>
      </main>
    </>
  );
}
