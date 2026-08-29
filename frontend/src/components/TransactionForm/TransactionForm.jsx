import { useEffect, useRef, useState } from "react";

import { listarCategorias } from "../../api/categorias";
import { listarContas } from "../../api/contas";
import { atualizarTransacao, criarTransacao } from "../../api/transacoes";
import { useEnterToNextField } from "../../hooks/useEnterToNextField";
import Dropdown from "../Dropdown/Dropdown";
import MultiSelect from "../MultiSelect/MultiSelect";
import "./TransactionForm.css";

function agora() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(
    d.getMinutes()
  )}`;
}

function valoresIniciais(initialValues) {
  if (!initialValues) {
    return {
      contaId: "",
      tipo: "saida",
      valor: "",
      data: agora(),
      descricao: "",
      categoriaIds: [],
    };
  }
  return {
    contaId: String(initialValues.conta_id),
    tipo: initialValues.tipo,
    valor: String(initialValues.valor),
    // A API devolve um datetime ISO completo ("YYYY-MM-DDTHH:mm:ss"); o
    // input datetime-local só aceita até os minutos.
    data: initialValues.data.slice(0, 16),
    descricao: initialValues.descricao ?? "",
    categoriaIds: (initialValues.categorias ?? []).map((categoria) => String(categoria.id)),
  };
}

export default function TransactionForm({ open, initialValues, onClose, onSaved }) {
  const dialogRef = useRef(null);
  const isEdit = Boolean(initialValues);
  const { ref: formRef, onKeyDown: handleFormKeyDown } = useEnterToNextField();

  const [contas, setContas] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [form, setForm] = useState(() => valoresIniciais(initialValues));
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    setForm(valoresIniciais(initialValues));
    setErrors({});
    setApiError(null);
  }, [open, initialValues]);

  useEffect(() => {
    if (!open) return;
    let cancelado = false;
    Promise.all([listarContas(), listarCategorias()])
      .then(([dadosContas, dadosCategorias]) => {
        if (cancelado) return;
        setContas(dadosContas);
        setCategorias(dadosCategorias);
      })
      .catch(() => {
        if (cancelado) return;
        setApiError("Não foi possível carregar contas/categorias.");
      });
    return () => {
      cancelado = true;
    };
  }, [open]);

  function validar() {
    const novosErros = {};
    if (!form.contaId) novosErros.contaId = "Selecione uma conta.";
    if (!form.tipo) novosErros.tipo = "Selecione o tipo.";
    const valorNumero = Number(form.valor);
    if (form.valor === "" || Number.isNaN(valorNumero) || valorNumero <= 0) {
      novosErros.valor = "O valor deve ser maior que zero.";
    }
    if (!form.data) novosErros.data = "Informe a data.";
    setErrors(novosErros);
    return Object.keys(novosErros).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError(null);
    if (!validar()) return;

    const dados = {
      conta_id: Number(form.contaId),
      tipo: form.tipo,
      valor: Number(form.valor),
      data: form.data,
      descricao: form.descricao.trim() === "" ? null : form.descricao,
      categoria_ids: form.categoriaIds.map(Number),
    };

    setSubmitting(true);
    try {
      if (isEdit) {
        await atualizarTransacao(initialValues.id, dados);
      } else {
        await criarTransacao({
          contaId: dados.conta_id,
          tipo: dados.tipo,
          valor: dados.valor,
          data: dados.data,
          descricao: dados.descricao,
          categoriaIds: dados.categoria_ids,
        });
      }
      onSaved();
    } catch (err) {
      if (err.response?.status === 422) {
        setApiError("Dados inválidos. Verifique os campos e tente novamente.");
      } else {
        setApiError("Não foi possível salvar a transação. Tente novamente.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="transaction-form-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <form
        className="transaction-form"
        onSubmit={handleSubmit}
        noValidate
        ref={formRef}
        onKeyDown={handleFormKeyDown}
      >
        <h2 className="transaction-form__title">
          {isEdit ? "Editar transação" : "Nova transação"}
        </h2>

        <label className="transaction-form__label" htmlFor="tf-conta">
          Conta
        </label>
        <Dropdown
          id="tf-conta"
          options={contas.map((conta) => ({ value: String(conta.id), label: conta.nome }))}
          value={form.contaId}
          onChange={(novoValor) => setForm((f) => ({ ...f, contaId: novoValor }))}
          placeholder="Selecione..."
        />
        {errors.contaId && <span className="transaction-form__error">{errors.contaId}</span>}

        <span className="transaction-form__label">Tipo</span>
        <div className="transaction-form__toggle">
          <button
            type="button"
            className={`transaction-form__toggle-btn ${
              form.tipo === "entrada" ? "transaction-form__toggle-btn--active-income" : ""
            }`}
            onClick={() => setForm((f) => ({ ...f, tipo: "entrada" }))}
          >
            Entrada
          </button>
          <button
            type="button"
            className={`transaction-form__toggle-btn ${
              form.tipo === "saida" ? "transaction-form__toggle-btn--active-expense" : ""
            }`}
            onClick={() => setForm((f) => ({ ...f, tipo: "saida" }))}
          >
            Saída
          </button>
        </div>
        {errors.tipo && <span className="transaction-form__error">{errors.tipo}</span>}

        <label className="transaction-form__label" htmlFor="tf-valor">
          Valor
        </label>
        <input
          id="tf-valor"
          className="transaction-form__input"
          type="number"
          step="0.01"
          min="0.01"
          value={form.valor}
          onChange={(event) => setForm((f) => ({ ...f, valor: event.target.value }))}
        />
        {errors.valor && <span className="transaction-form__error">{errors.valor}</span>}

        <label className="transaction-form__label" htmlFor="tf-data">
          Data e hora
        </label>
        <input
          id="tf-data"
          className="transaction-form__input"
          type="datetime-local"
          value={form.data}
          onChange={(event) => setForm((f) => ({ ...f, data: event.target.value }))}
        />
        {errors.data && <span className="transaction-form__error">{errors.data}</span>}

        <label className="transaction-form__label" htmlFor="tf-descricao">
          Descrição (opcional)
        </label>
        <input
          id="tf-descricao"
          className="transaction-form__input"
          type="text"
          value={form.descricao}
          onChange={(event) => setForm((f) => ({ ...f, descricao: event.target.value }))}
        />

        <span className="transaction-form__label">Categorias</span>
        <MultiSelect
          options={categorias.map((categoria) => ({
            value: String(categoria.id),
            label: categoria.nome,
            tipo: categoria.tipo,
          }))}
          value={form.categoriaIds}
          onChange={(novosIds) => setForm((f) => ({ ...f, categoriaIds: novosIds }))}
        />

        {apiError && <p className="transaction-form__api-error">{apiError}</p>}

        <div className="transaction-form__actions">
          <button
            type="button"
            className="transaction-form__button transaction-form__button--cancel"
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="transaction-form__button transaction-form__button--confirm"
            disabled={submitting}
          >
            {submitting ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
