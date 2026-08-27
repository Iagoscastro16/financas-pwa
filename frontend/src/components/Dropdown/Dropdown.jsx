import { useEffect, useRef, useState } from "react";

import { useClickOutside } from "../../hooks/useClickOutside";
import "./Dropdown.css";

export default function Dropdown({ id, options, value, onChange, placeholder = "Selecione..." }) {
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef(null);
  const listRef = useRef(null);

  useClickOutside(containerRef, () => setOpen(false));

  const selectedIndex = options.findIndex((option) => String(option.value) === String(value));
  const selectedOption = selectedIndex >= 0 ? options[selectedIndex] : null;

  function openList() {
    setOpen(true);
    setHighlightedIndex(selectedIndex >= 0 ? selectedIndex : 0);
  }

  function selectOption(option) {
    onChange(option.value);
    setOpen(false);
  }

  function handleKeyDown(event) {
    if (!open) {
      if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openList();
      }
      return;
    }

    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setHighlightedIndex((i) => Math.min(i + 1, options.length - 1));
        break;
      case "ArrowUp":
        event.preventDefault();
        setHighlightedIndex((i) => Math.max(i - 1, 0));
        break;
      case "Enter":
      case " ":
        event.preventDefault();
        if (options[highlightedIndex]) selectOption(options[highlightedIndex]);
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
    if (!open) return;
    const highlighted = listRef.current?.querySelector('[data-highlighted="true"]');
    highlighted?.scrollIntoView({ block: "nearest" });
  }, [open, highlightedIndex]);

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

      {open && (
        <ul className="dropdown__list" role="listbox" ref={listRef}>
          {options.length === 0 && <li className="dropdown__empty">Nenhuma opção.</li>}
          {options.map((option, index) => (
            <li
              key={option.value}
              role="option"
              aria-selected={index === selectedIndex}
              data-highlighted={index === highlightedIndex}
              className={`dropdown__option ${
                index === highlightedIndex ? "dropdown__option--highlighted" : ""
              } ${index === selectedIndex ? "dropdown__option--selected" : ""}`}
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
