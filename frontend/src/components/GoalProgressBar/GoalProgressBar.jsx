import { formatarMoeda } from "../../utils/format";
import "./GoalProgressBar.css";

export default function GoalProgressBar({ current, target }) {
  const percentual = target > 0 ? (current / target) * 100 : 0;
  // Visualmente nunca passa de 100% (nem fica negativo), mas o rótulo mostra
  // o percentual real, podendo passar de 100% quando a meta foi superada.
  const larguraVisual = Math.min(Math.max(percentual, 0), 100);

  return (
    <div className="goal-progress">
      <div className="goal-progress__track">
        <div className="goal-progress__fill" style={{ width: `${larguraVisual}%` }} />
      </div>
      <span className="goal-progress__label">
        {Math.round(percentual)}% concluído — {formatarMoeda(current)} / {formatarMoeda(target)}
      </span>
    </div>
  );
}
