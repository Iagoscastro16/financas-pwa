import { useEffect, useState } from "react";

import {
  cancelarTransacaoRecorrente,
  listarTransacoesRecorrentes,
} from "../../api/transacoesRecorrentes";
import RecurrenceList from "../RecurrenceList/RecurrenceList";
import RecurrenceForm from "../RecurrenceForm/RecurrenceForm";
import ConfirmDialog from "../ConfirmDialog/ConfirmDialog";
import "./RecurrenceManager.css";

export default function RecurrenceManager() {
  const [recorrencias, setRecorrencias] = useState([]);
  const [mostrarCanceladas, setMostrarCanceladas] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editando, setEditando] = useState(null);
  const [paraCancelar, setParaCancelar] = useState(null);

  async function recarregar() {
    setLoading(true);
    setError(null);
    try {
      const dados = await listarTransacoesRecorrentes({ includeInactive: mostrarCanceladas });
      setRecorrencias(dados);
    } catch {
      setError("Não foi possível carregar as recorrências. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);

    listarTransacoesRecorrentes({ includeInactive: mostrarCanceladas })
      .then((dados) => {
        if (cancelado) return;
        setRecorrencias(dados);
      })
      .catch(() => {
        if (cancelado) return;
        setError("Não foi possível carregar as recorrências. Tente novamente.");
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, [mostrarCanceladas]);

  function abrirNova() {
    setEditando(null);
    setFormOpen(true);
  }

  function abrirEdicao(recorrencia) {
    setEditando(recorrencia);
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

  async function confirmarCancelamento() {
    const idParaCancelar = paraCancelar.id;
    setParaCancelar(null);
    try {
      await cancelarTransacaoRecorrente(idParaCancelar);
      recarregar();
    } catch {
      setError("Não foi possível cancelar a recorrência. Tente novamente.");
    }
  }

  return (
    <div className="recurrence-manager">
      <div className="recurrence-manager__header">
        <label className="recurrence-manager__toggle">
          <input
            type="checkbox"
            checked={mostrarCanceladas}
            onChange={(event) => setMostrarCanceladas(event.target.checked)}
          />
          Mostrar canceladas
        </label>
        <button type="button" className="recurrence-manager__nova-btn" onClick={abrirNova}>
          + Nova recorrência
        </button>
      </div>

      <div className="card recurrence-manager__content">
        {error ? (
          <p className="recurrence-manager__error">{error}</p>
        ) : loading ? (
          <div className="skeleton recurrence-manager__skeleton" />
        ) : (
          <RecurrenceList
            recorrencias={recorrencias}
            onEdit={abrirEdicao}
            onCancel={setParaCancelar}
          />
        )}
      </div>

      <RecurrenceForm
        open={formOpen}
        initialValues={editando}
        onClose={fecharForm}
        onSaved={aoSalvar}
      />

      <ConfirmDialog
        open={Boolean(paraCancelar)}
        title="Cancelar recorrência?"
        message="As transações já geradas por esta recorrência não serão afetadas — só a criação de novas ocorrências nos próximos meses é interrompida."
        confirmLabel="Cancelar recorrência"
        cancelLabel="Voltar"
        onConfirm={confirmarCancelamento}
        onCancel={() => setParaCancelar(null)}
      />
    </div>
  );
}
