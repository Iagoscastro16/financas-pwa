import RecurrenceCard from "./RecurrenceCard";
import "./RecurrenceList.css";

export default function RecurrenceList({ recorrencias, onEdit, onCancel }) {
  if (!recorrencias || recorrencias.length === 0) {
    return <p className="recurrence-list__empty">Nenhuma recorrência cadastrada.</p>;
  }

  return (
    <ul className="recurrence-list">
      {recorrencias.map((recorrencia) => (
        <RecurrenceCard
          key={recorrencia.id}
          recorrencia={recorrencia}
          onEdit={onEdit}
          onCancel={onCancel}
        />
      ))}
    </ul>
  );
}
