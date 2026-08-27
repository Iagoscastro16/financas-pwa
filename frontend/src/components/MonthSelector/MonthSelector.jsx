import { mesAtual, nomeMesAno, somarMeses } from "../../utils/mesAno";
import "./MonthSelector.css";

export default function MonthSelector({ value, onChange }) {
  const podeAvancar = value !== mesAtual();

  return (
    <div className="month-selector">
      <button
        type="button"
        className="month-selector__arrow"
        onClick={() => onChange(somarMeses(value, -1))}
        aria-label="Mês anterior"
      >
        ←
      </button>
      <span className="month-selector__label">{nomeMesAno(value)}</span>
      <button
        type="button"
        className="month-selector__arrow"
        onClick={() => onChange(somarMeses(value, 1))}
        disabled={!podeAvancar}
        aria-label="Próximo mês"
      >
        →
      </button>
    </div>
  );
}
