import { formatarMoeda } from "../../utils/format";
import "./SummaryCard.css";

export default function SummaryCard({ entradas, saidas, loading }) {
  return (
    <div className="card summary-card">
      <div className="summary-card__item">
        <span className="summary-card__label">Entradas</span>
        {loading ? (
          <div className="skeleton summary-card__skeleton" />
        ) : (
          <span className="summary-card__value summary-card__value--income">
            {formatarMoeda(entradas)}
          </span>
        )}
      </div>
      <div className="summary-card__item">
        <span className="summary-card__label">Saídas</span>
        {loading ? (
          <div className="skeleton summary-card__skeleton" />
        ) : (
          <span className="summary-card__value summary-card__value--expense">
            {formatarMoeda(saidas)}
          </span>
        )}
      </div>
    </div>
  );
}
