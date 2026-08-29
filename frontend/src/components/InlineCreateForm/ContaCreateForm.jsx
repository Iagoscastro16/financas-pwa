import { useState } from "react";

import "./InlineCreateForm.css";

export default function ContaCreateForm({ onSubmit, onCancel, submitting, error }) {
  const [nome, setNome] = useState("");
  const [saldoInicial, setSaldoInicial] = useState("0");

  const saldoNumero = Number(saldoInicial);
  const valido = nome.trim() !== "" && saldoInicial !== "" && !Number.isNaN(saldoNumero);

  function submeter() {
    if (!valido) return;
    onSubmit({ nome: nome.trim(), saldoInicial: saldoNumero });
  }

  function handleKeyDown(event) {
    // Este componente é renderizado dentro do <form> do formulário "pai"
    // (TransactionForm). Por isso ele próprio NÃO é um <form> — <form>
    // dentro de <form> é inválido em HTML e faz o clique em "Criar"
    // disparar uma submissão nativa da página (perdendo o token JWT, que
    // só existe em memória). Enter aqui precisa ser tratado manualmente,
    // parando a propagação para não acionar a navegação por Enter do form
    // pai (useEnterToNextField) nem, em tese, um submit nativo.
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
        placeholder="Nome da conta"
        value={nome}
        onChange={(event) => setNome(event.target.value)}
        autoFocus
      />

      <span className="inline-create-form__field-label">Saldo inicial</span>
      <input
        type="number"
        step="0.01"
        className="inline-create-form__input"
        value={saldoInicial}
        onChange={(event) => setSaldoInicial(event.target.value)}
      />

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
