import { formatarMoeda } from "../../utils/format";
import "./BalanceCard.css";

export default function BalanceCard({ value, loading }) {
  return (
    <div className="card balance-card">
      <span className="balance-card__label">Saldo atual (todas as contas)</span>
      {loading ? (
        <div className="skeleton balance-card__skeleton" />
      ) : (
        <span className="balance-card__value">{formatarMoeda(value)}</span>
      )}
    </div>
  );
}
