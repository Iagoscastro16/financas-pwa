import { useRef, useState } from "react";

import CategoryBadge from "../CategoryBadge/CategoryBadge";
import { useClickOutside } from "../../hooks/useClickOutside";
import "./MultiSelect.css";

export default function MultiSelect({ options, value, onChange }) {
  const [open, setOpen] = useState(false);
  const [filtro, setFiltro] = useState("");
  const containerRef = useRef(null);
  const filterInputRef = useRef(null);

  useClickOutside(containerRef, () => setOpen(false));

  const selecionadas = options.filter((option) => value.includes(String(option.value)));
  const restantes = options.filter((option) => !value.includes(String(option.value)));

  const termoFiltro = filtro.trim().toLowerCase();
  const restantesFiltradas = termoFiltro
    ? restantes.filter((option) => option.label.toLowerCase().includes(termoFiltro))
    : restantes;

  function abrir() {
    setOpen(true);
    setFiltro("");
    requestAnimationFrame(() => filterInputRef.current?.focus());
  }

  function adicionar(optionValue) {
    onChange([...value, String(optionValue)]);
  }

  function remover(optionValue) {
    onChange(value.filter((v) => v !== String(optionValue)));
  }

  function handleFilterKeyDown(event) {
    if (event.key === "Enter" && restantesFiltradas.length > 0) {
      event.preventDefault();
      adicionar(restantesFiltradas[0].value);
      setFiltro("");
    } else if (event.key === "Escape") {
      // Mesmo motivo do Dropdown: sem isso o <dialog> nativo que envolve
      // este form também fecharia no mesmo Escape.
      event.preventDefault();
      setOpen(false);
    }
  }

  return (
    <div className="multiselect" ref={containerRef}>
      <div className="multiselect__chips">
        {selecionadas.map((option) => (
          <span key={option.value} className="multiselect__chip">
            <CategoryBadge categoria={{ nome: option.label, tipo: option.tipo }} />
            <button
              type="button"
              className="multiselect__remove"
              onClick={() => remover(option.value)}
              aria-label={`Remover ${option.label}`}
            >
              ×
            </button>
          </span>
        ))}
        <button type="button" className="multiselect__add-btn" onClick={abrir}>
          {selecionadas.length === 0 ? "Selecionar categorias..." : "+ Adicionar"}
        </button>
      </div>

      {open && (
        <div className="multiselect__dropdown">
          <input
            ref={filterInputRef}
            type="text"
            className="multiselect__filter"
            placeholder="Buscar categoria..."
            value={filtro}
            onChange={(event) => setFiltro(event.target.value)}
            onKeyDown={handleFilterKeyDown}
          />
          <ul className="multiselect__list" role="listbox">
            {restantesFiltradas.length === 0 && (
              <li className="multiselect__empty">Nenhuma categoria encontrada.</li>
            )}
            {restantesFiltradas.map((option) => (
              <li key={option.value} className="multiselect__option">
                <label className="multiselect__option-label">
                  <input type="checkbox" checked={false} onChange={() => adicionar(option.value)} />
                  {option.label}
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
