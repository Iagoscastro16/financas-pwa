import CategoryBadge from "../CategoryBadge/CategoryBadge";
import { formatarMoeda } from "../../utils/format";

function formatarData(dataIso) {
  const [ano, mes, dia] = dataIso.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

export default function RecurrenceCard({ recorrencia, onEdit, onCancel }) {
  const isEntrada = recorrencia.tipo === "entrada";

  return (
    <li className="recurrence-card">
      <div className="recurrence-card__header">
        <div className="recurrence-card__title-group">
          <span className="recurrence-card__nome">{recorrencia.nome}</span>
          <span
            className={`recurrence-card__status ${
              recorrencia.ativo
                ? "recurrence-card__status--ativo"
                : "recurrence-card__status--cancelada"
            }`}
          >
            {recorrencia.ativo ? "Ativa" : "Cancelada"}
          </span>
        </div>
        <div className="recurrence-card__actions">
          <button
            type="button"
            className="recurrence-card__action-btn"
            onClick={() => onEdit(recorrencia)}
            aria-label="Editar recorrência"
          >
            ✎
          </button>
          <button
            type="button"
            className="recurrence-card__action-btn recurrence-card__action-btn--danger"
            onClick={() => onCancel(recorrencia)}
            aria-label="Cancelar recorrência"
            disabled={!recorrencia.ativo}
          >
            🗑
          </button>
        </div>
      </div>

      <div className="recurrence-card__body">
        <span
          className={`recurrence-card__valor ${
            isEntrada ? "recurrence-card__valor--income" : "recurrence-card__valor--expense"
          }`}
        >
          {isEntrada ? "+" : "-"}
          {formatarMoeda(recorrencia.valor)}
        </span>
        <span className="recurrence-card__dia">todo dia {recorrencia.dia_mes}</span>
      </div>

      <div className="recurrence-card__periodo">
        Desde {formatarData(recorrencia.data_inicio)} até{" "}
        {recorrencia.data_fim ? formatarData(recorrencia.data_fim) : "sem data de término"}
      </div>

      {recorrencia.categorias?.length > 0 && (
        <div className="recurrence-card__categorias">
          {recorrencia.categorias.map((categoria) => (
            <CategoryBadge key={categoria.id} categoria={categoria} />
          ))}
        </div>
      )}
    </li>
  );
}
