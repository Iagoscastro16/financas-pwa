import { useEffect, useRef, useState } from "react";

import { criarCategoria, listarCategorias } from "../../api/categorias";
import { atualizarOrcamento, criarOrcamento } from "../../api/orcamentos";
import { nomeMesAno } from "../../utils/mesAno";
import { useEnterToNextField } from "../../hooks/useEnterToNextField";
import CategoriaCreateForm from "../InlineCreateForm/CategoriaCreateForm";
import Dropdown from "../Dropdown/Dropdown";
import "./BudgetForm.css";

function valoresIniciais(initialValues) {
  if (!initialValues) {
    return { categoriaId: "", valorMaximo: "" };
  }
  return {
    categoriaId: String(initialValues.categoria_id),
    valorMaximo: String(initialValues.valor_maximo),
  };
}

export default function BudgetForm({ open, initialValues, mesAno, onClose, onSaved }) {
  const dialogRef = useRef(null);
  const isEdit = Boolean(initialValues);
  const { ref: formRef, onKeyDown: handleFormKeyDown } = useEnterToNextField();

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
    listarCategorias()
      .then((dados) => {
        if (cancelado) return;
        setCategorias(dados);
      })
      .catch(() => {
        if (cancelado) return;
        setApiError("Não foi possível carregar categorias.");
      });
    return () => {
      cancelado = true;
    };
  }, [open]);

  function validar() {
    const novosErros = {};
    if (!form.categoriaId) novosErros.categoriaId = "Selecione uma categoria.";
    const valorNumero = Number(form.valorMaximo);
    if (form.valorMaximo === "" || Number.isNaN(valorNumero) || valorNumero <= 0) {
      novosErros.valorMaximo = "O valor máximo deve ser maior que zero.";
    }
    setErrors(novosErros);
    return Object.keys(novosErros).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError(null);
    if (!validar()) return;

    const dados = {
      categoria_id: Number(form.categoriaId),
      mes_ano: mesAno,
      valor_maximo: Number(form.valorMaximo),
    };

    setSubmitting(true);
    try {
      if (isEdit) {
        await atualizarOrcamento(initialValues.id, dados);
      } else {
        await criarOrcamento({
          categoriaId: dados.categoria_id,
          mesAno: dados.mes_ano,
          valorMaximo: dados.valor_maximo,
        });
      }
      onSaved();
    } catch (err) {
      if (err.response?.status === 400) {
        setApiError("Categoria não encontrada.");
      } else if (err.response?.status === 422) {
        setApiError("Dados inválidos. Verifique os campos e tente novamente.");
      } else {
        setApiError("Não foi possível salvar o orçamento. Tente novamente.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="budget-form-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <form
        className="budget-form"
        onSubmit={handleSubmit}
        noValidate
        ref={formRef}
        onKeyDown={handleFormKeyDown}
      >
        <h2 className="budget-form__title">{isEdit ? "Editar orçamento" : "Novo orçamento"}</h2>
        <p className="budget-form__mes">Mês: {nomeMesAno(mesAno)}</p>

        <label className="budget-form__label" htmlFor="bf-categoria">
          Categoria
        </label>
        <Dropdown
          id="bf-categoria"
          options={categorias.map((categoria) => ({
            value: String(categoria.id),
            label: categoria.nome,
          }))}
          value={form.categoriaId}
          onChange={(novoValor) => setForm((f) => ({ ...f, categoriaId: novoValor }))}
          placeholder="Selecione..."
          createNewLabel="+ Criar nova categoria"
          onCreateNew={async ({ nome, tipo }) => {
            const nova = await criarCategoria({ nome, tipo });
            setCategorias((atuais) => [...atuais, nova]);
            return { value: String(nova.id), label: nova.nome };
          }}
          renderCreateForm={(props) => <CategoriaCreateForm {...props} />}
        />
        {errors.categoriaId && <span className="budget-form__error">{errors.categoriaId}</span>}

        <label className="budget-form__label" htmlFor="bf-valor-maximo">
          Valor máximo
        </label>
        <input
          id="bf-valor-maximo"
          className="budget-form__input"
          type="number"
          step="0.01"
          min="0.01"
          value={form.valorMaximo}
          onChange={(event) => setForm((f) => ({ ...f, valorMaximo: event.target.value }))}
        />
        {errors.valorMaximo && <span className="budget-form__error">{errors.valorMaximo}</span>}

        {apiError && <p className="budget-form__api-error">{apiError}</p>}

        <div className="budget-form__actions">
          <button
            type="button"
            className="budget-form__button budget-form__button--cancel"
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="budget-form__button budget-form__button--confirm"
            disabled={submitting}
          >
            {submitting ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
