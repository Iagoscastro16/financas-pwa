import { useEffect, useRef, useState } from "react";

import { criarCategoria, listarCategorias } from "../../api/categorias";
import { criarConta, listarContas } from "../../api/contas";
import { atualizarTransacaoRecorrente, criarTransacaoRecorrente } from "../../api/transacoesRecorrentes";
import { useEnterToNextField } from "../../hooks/useEnterToNextField";
import CategoriaCreateForm from "../InlineCreateForm/CategoriaCreateForm";
import ContaCreateForm from "../InlineCreateForm/ContaCreateForm";
import Dropdown from "../Dropdown/Dropdown";
import MultiSelect from "../MultiSelect/MultiSelect";
import "./RecurrenceForm.css";

function hoje() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function valoresIniciais(initialValues) {
  if (!initialValues) {
    return {
      nome: "",
      valor: "",
      tipo: "saida",
      contaId: "",
      diaMes: String(new Date().getDate()),
      dataInicio: hoje(),
      dataFim: "",
      categoriaIds: [],
    };
  }
  return {
    nome: initialValues.nome,
    valor: String(initialValues.valor),
    tipo: initialValues.tipo,
    contaId: String(initialValues.conta_id),
    diaMes: String(initialValues.dia_mes),
    dataInicio: initialValues.data_inicio,
    dataFim: initialValues.data_fim ?? "",
    categoriaIds: (initialValues.categorias ?? []).map((categoria) => String(categoria.id)),
  };
}

export default function RecurrenceForm({ open, initialValues, onClose, onSaved }) {
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
    if (!form.nome.trim()) novosErros.nome = "Informe um nome.";

    const valorNumero = Number(form.valor);
    if (form.valor === "" || Number.isNaN(valorNumero) || valorNumero <= 0) {
      novosErros.valor = "O valor deve ser maior que zero.";
    }

    if (!isEdit && !form.contaId) novosErros.contaId = "Selecione uma conta.";

    const diaMesNumero = Number(form.diaMes);
    if (
      form.diaMes === "" ||
      !Number.isInteger(diaMesNumero) ||
      diaMesNumero < 1 ||
      diaMesNumero > 31
    ) {
      novosErros.diaMes = "Informe um dia entre 1 e 31.";
    }

    if (!isEdit && !form.dataInicio) novosErros.dataInicio = "Informe a data de início.";

    if (form.dataFim && form.dataInicio && form.dataFim < form.dataInicio) {
      novosErros.dataFim = "A data de término não pode ser anterior à data de início.";
    }

    setErrors(novosErros);
    return Object.keys(novosErros).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError(null);
    if (!validar()) return;

    setSubmitting(true);
    try {
      if (isEdit) {
        await atualizarTransacaoRecorrente(initialValues.id, {
          nome: form.nome.trim(),
          valor: Number(form.valor),
          dia_mes: Number(form.diaMes),
          data_fim: form.dataFim === "" ? null : form.dataFim,
          categoria_ids: form.categoriaIds.map(Number),
        });
      } else {
        await criarTransacaoRecorrente({
          nome: form.nome.trim(),
          valor: Number(form.valor),
          tipo: form.tipo,
          contaId: Number(form.contaId),
          diaMes: Number(form.diaMes),
          dataInicio: form.dataInicio,
          dataFim: form.dataFim === "" ? null : form.dataFim,
          categoriaIds: form.categoriaIds.map(Number),
        });
      }
      onSaved();
    } catch (err) {
      if (err.response?.status === 400) {
        setApiError("Conta ou categoria não encontrada.");
      } else if (err.response?.status === 422) {
        setApiError("Dados inválidos. Verifique os campos e tente novamente.");
      } else {
        setApiError("Não foi possível salvar a recorrência. Tente novamente.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="recurrence-form-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <form
        className="recurrence-form"
        onSubmit={handleSubmit}
        noValidate
        ref={formRef}
        onKeyDown={handleFormKeyDown}
      >
        <h2 className="recurrence-form__title">
          {isEdit ? "Editar recorrência" : "Nova recorrência"}
        </h2>

        <label className="recurrence-form__label" htmlFor="rf-nome">
          Nome
        </label>
        <input
          id="rf-nome"
          className="recurrence-form__input"
          type="text"
          value={form.nome}
          onChange={(event) => setForm((f) => ({ ...f, nome: event.target.value }))}
        />
        {errors.nome && <span className="recurrence-form__error">{errors.nome}</span>}

        <label className="recurrence-form__label" htmlFor="rf-valor">
          Valor
        </label>
        <input
          id="rf-valor"
          className="recurrence-form__input"
          type="number"
          step="0.01"
          min="0.01"
          value={form.valor}
          onChange={(event) => setForm((f) => ({ ...f, valor: event.target.value }))}
        />
        {errors.valor && <span className="recurrence-form__error">{errors.valor}</span>}

        <span className="recurrence-form__label">
          Tipo
          {isEdit && <span className="recurrence-form__locked-hint"> (não pode ser alterado)</span>}
        </span>
        <div className="recurrence-form__toggle">
          <button
            type="button"
            className={`recurrence-form__toggle-btn ${
              form.tipo === "entrada" ? "recurrence-form__toggle-btn--active-income" : ""
            }`}
            disabled={isEdit}
            onClick={() => setForm((f) => ({ ...f, tipo: "entrada" }))}
          >
            Entrada
          </button>
          <button
            type="button"
            className={`recurrence-form__toggle-btn ${
              form.tipo === "saida" ? "recurrence-form__toggle-btn--active-expense" : ""
            }`}
            disabled={isEdit}
            onClick={() => setForm((f) => ({ ...f, tipo: "saida" }))}
          >
            Saída
          </button>
        </div>

        <label className="recurrence-form__label" htmlFor="rf-conta">
          Conta
          {isEdit && <span className="recurrence-form__locked-hint"> (não pode ser alterada)</span>}
        </label>
        <Dropdown
          id="rf-conta"
          options={contas.map((conta) => ({ value: String(conta.id), label: conta.nome }))}
          value={form.contaId}
          onChange={(novoValor) => setForm((f) => ({ ...f, contaId: novoValor }))}
          placeholder="Selecione..."
          disabled={isEdit}
          createNewLabel="+ Criar nova conta"
          onCreateNew={async ({ nome, saldoInicial }) => {
            const nova = await criarConta({ nome, saldoInicial });
            setContas((atuais) => [...atuais, nova]);
            return { value: String(nova.id), label: nova.nome };
          }}
          renderCreateForm={(props) => <ContaCreateForm {...props} />}
        />
        {errors.contaId && <span className="recurrence-form__error">{errors.contaId}</span>}

        <label className="recurrence-form__label" htmlFor="rf-dia-mes">
          Dia do mês
        </label>
        <input
          id="rf-dia-mes"
          className="recurrence-form__input"
          type="number"
          min="1"
          max="31"
          step="1"
          value={form.diaMes}
          onChange={(event) => setForm((f) => ({ ...f, diaMes: event.target.value }))}
        />
        <span className="recurrence-form__hint">
          Se o mês não tiver esse dia (ex.: 31 em fevereiro), a transação é gerada no último dia
          do mês.
        </span>
        {errors.diaMes && <span className="recurrence-form__error">{errors.diaMes}</span>}

        <label className="recurrence-form__label" htmlFor="rf-data-inicio">
          Data de início
          {isEdit && <span className="recurrence-form__locked-hint"> (não pode ser alterada)</span>}
        </label>
        <input
          id="rf-data-inicio"
          className="recurrence-form__input"
          type="date"
          value={form.dataInicio}
          disabled={isEdit}
          onChange={(event) => setForm((f) => ({ ...f, dataInicio: event.target.value }))}
        />
        {errors.dataInicio && <span className="recurrence-form__error">{errors.dataInicio}</span>}

        <label className="recurrence-form__label" htmlFor="rf-data-fim">
          Data de término (opcional)
        </label>
        <input
          id="rf-data-fim"
          className="recurrence-form__input"
          type="date"
          value={form.dataFim}
          onChange={(event) => setForm((f) => ({ ...f, dataFim: event.target.value }))}
        />
        <span className="recurrence-form__hint">Deixe em branco para gerar até cancelar.</span>
        {errors.dataFim && <span className="recurrence-form__error">{errors.dataFim}</span>}

        <span className="recurrence-form__label">Categorias</span>
        <MultiSelect
          options={categorias.map((categoria) => ({
            value: String(categoria.id),
            label: categoria.nome,
            tipo: categoria.tipo,
          }))}
          value={form.categoriaIds}
          onChange={(novosIds) => setForm((f) => ({ ...f, categoriaIds: novosIds }))}
          createNewLabel="+ Criar nova categoria"
          onCreateNew={async ({ nome, tipo }) => {
            const nova = await criarCategoria({ nome, tipo });
            setCategorias((atuais) => [...atuais, nova]);
            return { value: String(nova.id), label: nova.nome, tipo: nova.tipo };
          }}
          renderCreateForm={(props) => <CategoriaCreateForm {...props} />}
        />

        {apiError && <p className="recurrence-form__api-error">{apiError}</p>}

        <div className="recurrence-form__actions">
          <button
            type="button"
            className="recurrence-form__button recurrence-form__button--cancel"
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="recurrence-form__button recurrence-form__button--confirm"
            disabled={submitting}
          >
            {submitting ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
