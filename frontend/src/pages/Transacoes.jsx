import { useEffect, useState } from "react";

import { listarTransacoes, removerTransacao } from "../api/transacoes";
import { mesAtual } from "../utils/mesAno";
import Dropdown from "../components/Dropdown/Dropdown";
import MonthSelector from "../components/MonthSelector/MonthSelector";
import TransactionList from "../components/TransactionList/TransactionList";
import TransactionForm from "../components/TransactionForm/TransactionForm";
import ConfirmDialog from "../components/ConfirmDialog/ConfirmDialog";
import "./Transacoes.css";

const OPCOES_ORDENACAO = [
  { value: "data_desc", label: "Mais recentes" },
  { value: "data_asc", label: "Mais antigas" },
  { value: "categoria", label: "Categoria (A-Z)" },
];

export default function Transacoes() {
  const [selectedMonth, setSelectedMonth] = useState(mesAtual());
  const [ordenarPor, setOrdenarPor] = useState("data_desc");
  const [transacoes, setTransacoes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editando, setEditando] = useState(null);
  const [transacaoParaExcluir, setTransacaoParaExcluir] = useState(null);

  async function recarregar() {
    setLoading(true);
    setError(null);
    try {
      const dados = await listarTransacoes({ mesAno: selectedMonth, ordenarPor });
      setTransacoes(dados);
    } catch {
      setError("Não foi possível carregar as transações. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);

    listarTransacoes({ mesAno: selectedMonth, ordenarPor })
      .then((dados) => {
        if (cancelado) return;
        setTransacoes(dados);
      })
      .catch(() => {
        if (cancelado) return;
        setError("Não foi possível carregar as transações. Tente novamente.");
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, [selectedMonth, ordenarPor]);

  function abrirNova() {
    setEditando(null);
    setFormOpen(true);
  }

  function abrirEdicao(transacao) {
    setEditando(transacao);
    setFormOpen(true);
  }

  function fecharForm() {
    setFormOpen(false);
    setEditando(null);
  }

  function aoSalvar() {
    fecharForm();
    recarregar();
  }

  async function confirmarExclusao() {
    const idParaExcluir = transacaoParaExcluir.id;
    setTransacaoParaExcluir(null);
    try {
      await removerTransacao(idParaExcluir);
      recarregar();
    } catch {
      setError("Não foi possível excluir a transação. Tente novamente.");
    }
  }

  return (
    <div className="transacoes-page">
      <div className="transacoes-page__header">
        <div className="transacoes-page__filters">
          <MonthSelector value={selectedMonth} onChange={setSelectedMonth} />
          <Dropdown
            id="ordenar-por"
            options={OPCOES_ORDENACAO}
            value={ordenarPor}
            onChange={setOrdenarPor}
          />
        </div>
        <button type="button" className="transacoes-page__nova-btn" onClick={abrirNova}>
          + Nova transação
        </button>
      </div>

      <div className="card transacoes-page__content">
        {error ? (
          <p className="transacoes-page__error">{error}</p>
        ) : loading ? (
          <div className="skeleton transacoes-page__skeleton" />
        ) : (
          <TransactionList
            transacoes={transacoes}
            onEdit={abrirEdicao}
            onDelete={setTransacaoParaExcluir}
          />
        )}
      </div>

      <TransactionForm
        open={formOpen}
        initialValues={editando}
        onClose={fecharForm}
        onSaved={aoSalvar}
      />

      <ConfirmDialog
        open={Boolean(transacaoParaExcluir)}
        title="Excluir transação?"
        message="Essa ação não pode ser desfeita."
        confirmLabel="Excluir"
        onConfirm={confirmarExclusao}
        onCancel={() => setTransacaoParaExcluir(null)}
      />
    </div>
  );
}
