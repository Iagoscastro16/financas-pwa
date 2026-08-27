import CategoryBadge from "../CategoryBadge/CategoryBadge";
import { formatarMoeda } from "../../utils/format";

function formatarData(dataIso) {
  const [ano, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}/${ano}`;
}

export default function TransactionRow({ transacao, onEdit, onDelete }) {
  const isEntrada = transacao.tipo === "entrada";

  return (
    <li className="transaction-row">
      <div className="transaction-row__main">
        <span className="transaction-row__data">{formatarData(transacao.data)}</span>
        <span className="transaction-row__descricao">
          {transacao.descricao || "(sem descrição)"}
        </span>
        {transacao.categorias.length > 0 && (
          <div className="transaction-row__categorias">
            {transacao.categorias.map((categoria) => (
              <CategoryBadge key={categoria.id} categoria={categoria} />
            ))}
          </div>
        )}
      </div>
      <div className="transaction-row__side">
        <span
          className={`transaction-row__valor ${
            isEntrada ? "transaction-row__valor--income" : "transaction-row__valor--expense"
          }`}
        >
          {isEntrada ? "+" : "-"}
          {formatarMoeda(transacao.valor)}
        </span>
        <div className="transaction-row__actions">
          <button
            type="button"
            className="transaction-row__action-btn"
            onClick={() => onEdit(transacao)}
            aria-label="Editar transação"
          >
            ✎
          </button>
          <button
            type="button"
            className="transaction-row__action-btn transaction-row__action-btn--danger"
            onClick={() => onDelete(transacao)}
            aria-label="Excluir transação"
          >
            🗑
          </button>
        </div>
      </div>
    </li>
  );
}
