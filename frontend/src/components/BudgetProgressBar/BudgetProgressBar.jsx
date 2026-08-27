import { formatarMoeda } from "../../utils/format";
import "./BudgetProgressBar.css";

export default function BudgetProgressBar({ spent, limit, alertThreshold }) {
  const percentual = limit > 0 ? (spent / limit) * 100 : 0;
  const larguraVisual = Math.min(percentual, 100);

  let estado = "ok";
  if (percentual > 100) {
    estado = "over";
  } else if (percentual >= alertThreshold) {
    estado = "warning";
  }

  let texto = `${Math.round(percentual)}% — ${formatarMoeda(spent)} / ${formatarMoeda(limit)}`;
  if (estado === "over") {
    texto += ` (${formatarMoeda(spent - limit)} acima do limite)`;
  }

  return (
    <div className="budget-progress">
      <div className="budget-progress__track">
        <div
          className={`budget-progress__fill budget-progress__fill--${estado}`}
          style={{ width: `${larguraVisual}%` }}
        />
      </div>
      <span className={`budget-progress__label budget-progress__label--${estado}`}>{texto}</span>
    </div>
  );
}
