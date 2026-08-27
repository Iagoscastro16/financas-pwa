import { useEffect, useState } from "react";

import { listarMetas, removerMeta } from "../api/metas";
import { formatarMoeda } from "../utils/format";
import { calcularNecessarioPorMes } from "../utils/metas";
import GoalProgressBar from "../components/GoalProgressBar/GoalProgressBar";
import MetaForm from "../components/MetaForm/MetaForm";
import ConfirmDialog from "../components/ConfirmDialog/ConfirmDialog";
import "./Metas.css";

function formatarData(dataIso) {
  const [ano, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}/${ano}`;
}

export default function Metas() {
  const [metas, setMetas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editando, setEditando] = useState(null);
  const [metaParaExcluir, setMetaParaExcluir] = useState(null);

  async function recarregar() {
    setLoading(true);
    setError(null);
    try {
      const dados = await listarMetas();
      setMetas(dados);
    } catch {
      setError("Não foi possível carregar as metas. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  // Metas não são recortadas por mês, então é uma busca única no mount, sem
  // o padrão de re-fetch por seletor de mês usado nas outras páginas.
  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);

    listarMetas()
      .then((dados) => {
        if (cancelado) return;
        setMetas(dados);
      })
      .catch(() => {
        if (cancelado) return;
        setError("Não foi possível carregar as metas. Tente novamente.");
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, []);

  function abrirNova() {
    setEditando(null);
    setFormOpen(true);
  }

  function abrirEdicao(meta) {
    setEditando(meta);
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
    const idParaExcluir = metaParaExcluir.id;
    setMetaParaExcluir(null);
    try {
      await removerMeta(idParaExcluir);
      recarregar();
    } catch {
      setError("Não foi possível excluir a meta. Tente novamente.");
    }
  }

  return (
    <div className="metas-page">
      <div className="metas-page__header">
        <h1 className="metas-page__title">Metas</h1>
        <button type="button" className="metas-page__nova-btn" onClick={abrirNova}>
          + Nova meta
        </button>
      </div>

      <div className="card metas-page__content">
        {error ? (
          <p className="metas-page__error">{error}</p>
        ) : loading ? (
          <div className="skeleton metas-page__skeleton" />
        ) : metas.length === 0 ? (
          <p className="metas-page__empty">Nenhuma meta cadastrada.</p>
        ) : (
          <ul className="metas-page__list">
            {metas.map((meta) => {
              const necessario = calcularNecessarioPorMes(meta);
              return (
                <li key={meta.id} className="meta-card">
                  <div className="meta-card__header">
                    <span className="meta-card__nome">{meta.nome}</span>
                    <div className="meta-card__actions">
                      <button
                        type="button"
                        className="meta-card__action-btn"
                        onClick={() => abrirEdicao(meta)}
                        aria-label="Editar meta"
                      >
                        ✎
                      </button>
                      <button
                        type="button"
                        className="meta-card__action-btn meta-card__action-btn--danger"
                        onClick={() => setMetaParaExcluir(meta)}
                        aria-label="Excluir meta"
                      >
                        🗑
                      </button>
                    </div>
                  </div>

                  <GoalProgressBar current={meta.valor_atual} target={meta.valor_alvo} />

                  <div className="meta-card__footer">
                    {meta.prazo && (
                      <span className="meta-card__prazo">Prazo: {formatarData(meta.prazo)}</span>
                    )}
                    {necessario.status === "concluida" && (
                      <span className="meta-card__necessario meta-card__necessario--concluida">
                        Meta concluída
                      </span>
                    )}
                    {necessario.status === "vencido" && (
                      <span className="meta-card__necessario meta-card__necessario--vencido">
                        Prazo vencido
                      </span>
                    )}
                    {necessario.status === "ok" && (
                      <span className="meta-card__necessario">
                        Necessário {formatarMoeda(necessario.valorNecessario)}/mês
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <MetaForm open={formOpen} initialValues={editando} onClose={fecharForm} onSaved={aoSalvar} />

      <ConfirmDialog
        open={Boolean(metaParaExcluir)}
        title="Excluir meta?"
        message="Essa ação não pode ser desfeita."
        confirmLabel="Excluir"
        onConfirm={confirmarExclusao}
        onCancel={() => setMetaParaExcluir(null)}
      />
    </div>
  );
}
