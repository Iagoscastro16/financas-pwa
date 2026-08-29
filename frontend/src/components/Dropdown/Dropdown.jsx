import { useEffect, useRef, useState } from "react";

import { useClickOutside } from "../../hooks/useClickOutside";
import { extrairMensagemErro } from "../../utils/erros";
import "./Dropdown.css";

const CREATE_NEW_VALUE = "__criar_novo__";

export default function Dropdown({
  id,
  options,
  value,
  onChange,
  placeholder = "Selecione...",
  onCreateNew,
  createNewLabel = "+ Criar novo",
  renderCreateForm,
}) {
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [criando, setCriando] = useState(false);
  const [submetendoCriacao, setSubmetendoCriacao] = useState(false);
  const [erroCriacao, setErroCriacao] = useState(null);
  const containerRef = useRef(null);
  const listRef = useRef(null);

  useClickOutside(containerRef, () => setOpen(false));

  const opcoesNavegaveis =
    onCreateNew && !criando
      ? [...options, { value: CREATE_NEW_VALUE, label: createNewLabel, criarNovo: true }]
      : options;

  const selectedIndex = options.findIndex((option) => String(option.value) === String(value));
  const selectedOption = selectedIndex >= 0 ? options[selectedIndex] : null;

  function openList() {
    setOpen(true);
    setCriando(false);
    setErroCriacao(null);
    setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0);
  }

  function selectOption(option) {
    if (option.criarNovo) {
      setCriando(true);
      return;
    }
    onChange(option.value);
    setOpen(false);
  }

  async function handleCreateSubmit(payload) {
    setSubmetendoCriacao(true);
    setErroCriacao(null);
    try {
      const novaOpcao = await onCreateNew(payload);
      onChange(novaOpcao.value);
      setCriando(false);
      setOpen(false);
    } catch (err) {
      setErroCriacao(extrairMensagemErro(err));
    } finally {
      setSubmetendoCriacao(false);
    }
  }

  function handleKeyDown(event) {
    if (!open) {
      if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openList();
      }
      return;
    }

    if (criando) {
      if (event.key === "Escape") {
        event.preventDefault();
        setCriando(false);
      }
      return;
    }

    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setHighlightedIndex((i) => Math.min(i + 1, opcoesNavegaveis.length - 1));
        break;
      case "ArrowUp":
        event.preventDefault();
        setHighlightedIndex((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        if (opcoesNavegaveis[highlightedIndex]) selectOption(opcoesNavegaveis[highlightedIndex]);
        break;
      case "Tab":
        setOpen(false);
        break;
      case "Escape":
        // Sem isso, o keydown chega ao <dialog> nativo que envolve este
        // form e fecha o MODAL INTEIRO (comportamento padrão de Escape em
        // <dialog>), quando a intenção aqui é fechar só a lista aberta —
        // useClickOutside cuida do fechamento em si, este preventDefault só
        // impede que o <dialog> também reaja ao mesmo Escape.
        event.preventDefault();
        setOpen(false);
        break;
      default:
        break;
    }
  }

  useEffect(() => {
    if (!open || criando) return;
    const highlighted = listRef.current?.querySelector('[data-highlighted="true"]');
    highlighted?.scrollIntoView({ block: "nearest" });
  }, [open, criando, highlightedIndex]);

  return (
    <div className="dropdown" ref={containerRef}>
      <button
        id={id}
        type="button"
        className="dropdown__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={handleKeyDown}
      >
        <span className={selectedOption ? "dropdown__value" : "dropdown__placeholder"}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <span className="dropdown__caret" aria-hidden="true">
          ▾
        </span>
      </button>

      {open && criando && (
        <div className="dropdown__create-form">
          {renderCreateForm({
            onSubmit: handleCreateSubmit,
            onCancel: () => {
              setCriando(false);
              setErroCriacao(null);
            },
            submitting: submetendoCriacao,
            error: erroCriacao,
          })}
        </div>
      )}

      {open && !criando && (
        <ul className="dropdown__list" role="listbox" ref={listRef}>
          {options.length === 0 && !onCreateNew && (
            <li className="dropdown__empty">Nenhuma opção.</li>
          )}
          {opcoesNavegaveis.map((option, index) => (
            <li
              key={option.value}
              role="option"
              aria-selected={index === selectedIndex}
              data-highlighted={index === highlightedIndex}
              className={`dropdown__option ${
                index === highlightedIndex ? "dropdown__option--highlighted" : ""
              } ${index === selectedIndex ? "dropdown__option--selected" : ""} ${
                option.criarNovo ? "dropdown__option--create-new" : ""
              }`}
              onMouseEnter={() => setHighlightedIndex(index)}
              onClick={() => selectOption(option)}
            >
              {option.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
