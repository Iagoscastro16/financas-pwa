import { useEffect, useState } from "react";

import { listarCategorias } from "../api/categorias";
import { obterConfiguracao } from "../api/configuracao";
import { listarOrcamentos, removerOrcamento } from "../api/orcamentos";
import { resumoCategorias } from "../api/resumo";
import { mesAtual } from "../utils/mesAno";
import MonthSelector from "../components/MonthSelector/MonthSelector";
import BudgetProgressBar from "../components/BudgetProgressBar/BudgetProgressBar";
import BudgetForm from "../components/BudgetForm/BudgetForm";
import ConfirmDialog from "../components/ConfirmDialog/ConfirmDialog";
import "./Orcamentos.css";

const LIMITE_ALERTA_PADRAO = 80;

export default function Orcamentos() {
  const [selectedMonth, setSelectedMonth] = useState(mesAtual());
  const [orcamentos, setOrcamentos] = useState([]);
  const [gastos, setGastos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [alertThreshold, setAlertThreshold] = useState(LIMITE_ALERTA_PADRAO);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [formOpen, setFormOpen] = useState(false);
  const [editando, setEditando] = useState(null);
  const [orcamentoParaExcluir, setOrcamentoParaExcluir] = useState(null);

  // Categorias e o limiar de alerta raramente mudam — buscados uma única vez
  // no mount, não a cada troca de mês (diferente de orçamentos/gastos).
  useEffect(() => {
    let cancelado = false;

    listarCategorias().then((dados) => {
      if (!cancelado) setCategorias(dados);
    });
    // Falha ao carregar categorias não é crítica: os cards caem no fallback
    // "Categoria #id" em vez de travar a página inteira.

    obterConfiguracao("orcamento_limite_alerta_percentual")
      .then((config) => {
        if (cancelado) return;
        const numero = Number(config.valor);
        setAlertThreshold(Number.isFinite(numero) ? numero : LIMITE_ALERTA_PADRAO);
      })
      .catch(() => {
        if (!cancelado) setAlertThreshold(LIMITE_ALERTA_PADRAO);
      });

    return () => {
      cancelado = true;
    };
  }, []);

  async function recarregar() {
    setLoading(true);
    setError(null);
    try {
      const [dadosOrcamentos, dadosGastos] = await Promise.all([
        listarOrcamentos({ mesAno: selectedMonth }),
        resumoCategorias({ mesAno: selectedMonth }),
      ]);
      setOrcamentos(dadosOrcamentos);
      setGastos(dadosGastos);
    } catch {
      setError("Não foi possível carregar os orçamentos. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);

    Promise.all([
      listarOrcamentos({ mesAno: selectedMonth }),
      resumoCategorias({ mesAno: selectedMonth }),
    ])
      .then(([dadosOrcamentos, dadosGastos]) => {
        if (cancelado) return;
        setOrcamentos(dadosOrcamentos);
        setGastos(dadosGastos);
      })
      .catch(() => {
        if (cancelado) return;
        setError("Não foi possível carregar os orçamentos. Tente novamente.");
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, [selectedMonth]);

  function abrirNovo() {
    setEditando(null);
    setFormOpen(true);
  }

  function abrirEdicao(orcamento) {
    setEditando(orcamento);
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
    const idParaExcluir = orcamentoParaExcluir.id;
    setOrcamentoParaExcluir(null);
    try {
      await removerOrcamento(idParaExcluir);
      recarregar();
    } catch {
      setError("Não foi possível excluir o orçamento. Tente novamente.");
    }
  }

  // Combina os orçamentos do mês com o gasto real por categoria
  // (/resumo/categorias só lista categorias com gasto > 0 no mês, então uma
  // categoria orçada sem nenhum gasto ainda cai no fallback 0) e com o nome
  // da categoria (não vem em /orcamentos, só o categoria_id).
  const gastoPorCategoriaId = new Map(
    gastos.filter((g) => g.categoria_id !== null).map((g) => [g.categoria_id, g.total]),
  );
  const categoriaPorId = new Map(categorias.map((c) => [c.id, c]));

  const itens = orcamentos.map((orcamento) => ({
    ...orcamento,
    categoriaNome:
      categoriaPorId.get(orcamento.categoria_id)?.nome ?? `Categoria #${orcamento.categoria_id}`,
    spent: gastoPorCategoriaId.get(orcamento.categoria_id) ?? 0,
  }));

  return (
    <div className="orcamentos-page">
      <div className="orcamentos-page__header">
        <MonthSelector value={selectedMonth} onChange={setSelectedMonth} />
        <button type="button" className="orcamentos-page__novo-btn" onClick={abrirNovo}>
          + Novo orçamento
        </button>
      </div>

      <div className="card orcamentos-page__content">
        {error ? (
          <p className="orcamentos-page__error">{error}</p>
        ) : loading ? (
          <div className="skeleton orcamentos-page__skeleton" />
        ) : itens.length === 0 ? (
          <p className="orcamentos-page__empty">Nenhum orçamento definido para este mês.</p>
        ) : (
          <ul className="orcamentos-page__list">
            {itens.map((item) => (
              <li key={item.id} className="orcamento-card">
                <div className="orcamento-card__header">
                  <span className="orcamento-card__categoria">{item.categoriaNome}</span>
                  <div className="orcamento-card__actions">
                    <button
                      type="button"
                      className="orcamento-card__action-btn"
                      onClick={() => abrirEdicao(item)}
                      aria-label="Editar orçamento"
                    >
                      ✎
                    </button>
                    <button
                      type="button"
                      className="orcamento-card__action-btn orcamento-card__action-btn--danger"
                      onClick={() => setOrcamentoParaExcluir(item)}
                      aria-label="Excluir orçamento"
                    >
                      🗑
                    </button>
                  </div>
                </div>
                <BudgetProgressBar
                  spent={item.spent}
                  limit={item.valor_maximo}
                  alertThreshold={alertThreshold}
                />
              </li>
            ))}
          </ul>
        )}
      </div>

      <BudgetForm
        open={formOpen}
        initialValues={editando}
        mesAno={selectedMonth}
        onClose={fecharForm}
        onSaved={aoSalvar}
      />

      <ConfirmDialog
        open={Boolean(orcamentoParaExcluir)}
        title="Excluir orçamento?"
        message="Essa ação não pode ser desfeita."
        confirmLabel="Excluir"
        onConfirm={confirmarExclusao}
        onCancel={() => setOrcamentoParaExcluir(null)}
      />
    </div>
  );
}
