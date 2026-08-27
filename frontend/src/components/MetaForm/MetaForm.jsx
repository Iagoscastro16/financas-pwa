import { useEffect, useRef, useState } from "react";

import { atualizarMeta, criarMeta } from "../../api/metas";
import "./MetaForm.css";

function valoresIniciais(initialValues) {
  if (!initialValues) {
    return { nome: "", valorAlvo: "", valorAtual: "0", prazo: "" };
  }
  return {
    nome: initialValues.nome,
    valorAlvo: String(initialValues.valor_alvo),
    valorAtual: String(initialValues.valor_atual),
    prazo: initialValues.prazo ?? "",
  };
}

export default function MetaForm({ open, initialValues, onClose, onSaved }) {
  const dialogRef = useRef(null);
  const isEdit = Boolean(initialValues);

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

  function validar() {
    const novosErros = {};
    if (!form.nome.trim()) novosErros.nome = "Informe um nome.";

    const valorAlvoNumero = Number(form.valorAlvo);
    if (form.valorAlvo === "" || Number.isNaN(valorAlvoNumero) || valorAlvoNumero <= 0) {
      novosErros.valorAlvo = "O valor alvo deve ser maior que zero.";
    }

    const valorAtualNumero = Number(form.valorAtual);
    if (form.valorAtual === "" || Number.isNaN(valorAtualNumero) || valorAtualNumero < 0) {
      novosErros.valorAtual = "O valor atual não pode ser negativo.";
    }

    setErrors(novosErros);
    return Object.keys(novosErros).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError(null);
    if (!validar()) return;

    const dados = {
      nome: form.nome.trim(),
      valor_alvo: Number(form.valorAlvo),
      valor_atual: Number(form.valorAtual),
      prazo: form.prazo === "" ? null : form.prazo,
    };

    setSubmitting(true);
    try {
      if (isEdit) {
        await atualizarMeta(initialValues.id, dados);
      } else {
        await criarMeta({
          nome: dados.nome,
          valorAlvo: dados.valor_alvo,
          valorAtual: dados.valor_atual,
          prazo: dados.prazo,
        });
      }
      onSaved();
    } catch (err) {
      if (err.response?.status === 422) {
        setApiError("Dados inválidos. Verifique os campos e tente novamente.");
      } else {
        setApiError("Não foi possível salvar a meta. Tente novamente.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="meta-form-dialog"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <form className="meta-form" onSubmit={handleSubmit} noValidate>
        <h2 className="meta-form__title">{isEdit ? "Editar meta" : "Nova meta"}</h2>

        <label className="meta-form__label" htmlFor="mf-nome">
          Nome
        </label>
        <input
          id="mf-nome"
          className="meta-form__input"
          type="text"
          value={form.nome}
          onChange={(event) => setForm((f) => ({ ...f, nome: event.target.value }))}
        />
        {errors.nome && <span className="meta-form__error">{errors.nome}</span>}

        <label className="meta-form__label" htmlFor="mf-valor-alvo">
          Valor alvo
        </label>
        <input
          id="mf-valor-alvo"
          className="meta-form__input"
          type="number"
          step="0.01"
          min="0.01"
          value={form.valorAlvo}
          onChange={(event) => setForm((f) => ({ ...f, valorAlvo: event.target.value }))}
        />
        {errors.valorAlvo && <span className="meta-form__error">{errors.valorAlvo}</span>}

        <label className="meta-form__label" htmlFor="mf-valor-atual">
          Valor atual
        </label>
        <input
          id="mf-valor-atual"
          className="meta-form__input"
          type="number"
          step="0.01"
          min="0"
          value={form.valorAtual}
          onChange={(event) => setForm((f) => ({ ...f, valorAtual: event.target.value }))}
        />
        {errors.valorAtual && <span className="meta-form__error">{errors.valorAtual}</span>}

        <label className="meta-form__label" htmlFor="mf-prazo">
          Prazo (opcional)
        </label>
        <input
          id="mf-prazo"
          className="meta-form__input"
          type="date"
          value={form.prazo}
          onChange={(event) => setForm((f) => ({ ...f, prazo: event.target.value }))}
        />

        {apiError && <p className="meta-form__api-error">{apiError}</p>}

        <div className="meta-form__actions">
          <button
            type="button"
            className="meta-form__button meta-form__button--cancel"
            onClick={onClose}
            disabled={submitting}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="meta-form__button meta-form__button--confirm"
            disabled={submitting}
          >
            {submitting ? "Salvando..." : "Salvar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
