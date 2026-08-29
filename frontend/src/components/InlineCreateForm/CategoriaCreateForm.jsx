import { useState } from "react";

import "./InlineCreateForm.css";

export default function CategoriaCreateForm({ onSubmit, onCancel, submitting, error }) {
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("despesa");

  const valido = nome.trim() !== "";

  function submeter() {
    if (!valido) return;
    onSubmit({ nome: nome.trim(), tipo });
  }

  function handleKeyDown(event) {
    // Não é um <form>: este componente é renderizado dentro do <form> do
    // formulário "pai" (TransactionForm/BudgetForm), e <form> dentro de
    // <form> é inválido em HTML — o clique em "Criar" acabaria disparando
    // uma submissão nativa da página, perdendo o token JWT (que só existe
    // em memória). Enter é tratado manualmente aqui, parando a propagação
    // para não acionar a navegação por Enter do form pai.
    if (event.key === "Enter") {
      event.preventDefault();
      event.stopPropagation();
      submeter();
    } else if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      onCancel();
    }
  }

  return (
    <div className="inline-create-form" onKeyDown={handleKeyDown}>
      <input
        type="text"
        className="inline-create-form__input"
        placeholder="Nome da categoria"
        value={nome}
        onChange={(event) => setNome(event.target.value)}
        autoFocus
      />

      <div className="inline-create-form__toggle">
        <button
          type="button"
          className={`inline-create-form__toggle-btn ${
            tipo === "receita" ? "inline-create-form__toggle-btn--active-income" : ""
          }`}
          onClick={() => setTipo("receita")}
        >
          Receita
        </button>
        <button
          type="button"
          className={`inline-create-form__toggle-btn ${
            tipo === "despesa" ? "inline-create-form__toggle-btn--active-expense" : ""
          }`}
          onClick={() => setTipo("despesa")}
        >
          Despesa
        </button>
      </div>

      {error && <p className="inline-create-form__error">{error}</p>}

      <div className="inline-create-form__actions">
        <button
          type="button"
          className="inline-create-form__button"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancelar
        </button>
        <button
          type="button"
          className="inline-create-form__button inline-create-form__button--confirm"
          onClick={submeter}
          disabled={submitting || !valido}
        >
          {submitting ? "Criando..." : "Criar"}
        </button>
      </div>
    </div>
  );
}
