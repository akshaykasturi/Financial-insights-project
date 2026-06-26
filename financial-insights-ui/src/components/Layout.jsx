import { NavLink, Outlet } from "react-router-dom";
import { MessageSquare, LayoutDashboard, Settings, TrendingUp } from "lucide-react";
import TickerTape from "./TickerTape";

const navItems = [
  { to: "/", label: "Insights Chat", icon: MessageSquare },
  { to: "/dashboard", label: "Market Dashboard", icon: LayoutDashboard },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-ink">
      <TickerTape />

      <header className="border-b hairline px-6 md:px-10 py-5 flex items-center justify-between">
        <div className="flex items-baseline gap-3">
          <TrendingUp className="w-6 h-6 text-brass" strokeWidth={1.75} />
          <h1 className="font-display text-2xl md:text-[26px] font-medium tracking-tight text-paper">
            Nifty<span className="text-gradient-brass"> Insights</span>
          </h1>
          <h1 className="font-display text-lg md:text-[26px] font-medium tracking-tight text-paper"> </h1>
          <span className="hidden md:inline text-[11px] font-mono-data uppercase tracking-[0.18em] text-slate-light ml-1">
            Agentic Intelligence · Est. data 1998
          </span>
        </div>

        <nav className="flex items-center gap-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-colors duration-150 ${
                  isActive
                    ? "bg-ink-card text-brass"
                    : "text-slate-light hover:text-paper hover:bg-ink-card/60"
                }`
              }
            >
              <Icon className="w-4 h-4" strokeWidth={1.75} />
              <span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-2.5 rounded-md text-sm transition-colors duration-150 ml-2 border hairline ${
                isActive
                  ? "bg-ink-card text-brass"
                  : "text-slate-light/70 hover:text-slate-light"
              }`
            }
            title="Admin"
          >
            <Settings className="w-4 h-4" strokeWidth={1.75} />
          </NavLink>
        </nav>
      </header>

      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}
