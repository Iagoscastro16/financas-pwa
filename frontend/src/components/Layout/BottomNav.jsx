import { NavLink } from "react-router-dom";

import { NAV_LINKS } from "./navLinks";
import "./BottomNav.css";

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      {NAV_LINKS.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            isActive ? "bottom-nav__link bottom-nav__link--active" : "bottom-nav__link"
          }
        >
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
