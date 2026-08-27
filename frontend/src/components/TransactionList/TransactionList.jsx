import TransactionRow from "./TransactionRow";
import "./TransactionList.css";

export default function TransactionList({ transacoes, onEdit, onDelete }) {
  if (!transacoes || transacoes.length === 0) {
    return <p className="transaction-list__empty">Nenhuma transação neste mês.</p>;
  }

  return (
    <ul className="transaction-list">
      {transacoes.map((transacao) => (
        <TransactionRow
          key={transacao.id}
          transacao={transacao}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </ul>
  );
}
