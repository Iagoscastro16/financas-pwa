import { useRef } from "react";

// Tipos de <input> considerados "campo de texto" para fins de navegação por
// Enter. Propositalmente não inclui checkbox/radio/button/etc., e um
// <textarea> nunca bate aqui (Enter precisa continuar quebrando linha nele).
const ADVANCE_TYPES = new Set(["text", "number", "date", "email", "password", "tel", "url", "search"]);

/**
 * Faz Enter, num <input> de texto/número/data dentro do form, mover o foco
 * para o próximo campo do tipo em vez de submeter — exceto no último campo,
 * onde Enter dispara o submit (equivalente a clicar em Salvar/Entrar).
 *
 * Dropdown e MultiSelect têm seu próprio tratamento de Enter (abrir lista,
 * selecionar opção destacada). Para não interferir com isso, ignoramos
 * Enter em qualquer campo dentro de `.dropdown`/`.multiselect`, e também
 * respeitamos `event.defaultPrevented` caso algum outro widget já tenha
 * tratado a tecla.
 *
 * Uso: const enterNav = useEnterToNextField(); <form ref={enterNav.ref} onKeyDown={enterNav.onKeyDown}>
 */
export function useEnterToNextField() {
  const formRef = useRef(null);

  function handleKeyDown(event) {
    if (event.key !== "Enter" || event.defaultPrevented) return;

    const target = event.target;
    if (target.tagName !== "INPUT" || !ADVANCE_TYPES.has(target.type)) return;
    if (target.closest(".dropdown, .multiselect")) return;

    const form = formRef.current;
    if (!form) return;

    const campos = Array.from(
      form.querySelectorAll(
        Array.from(ADVANCE_TYPES)
          .map((type) => `input[type="${type}"]`)
          .join(", "),
      ),
    ).filter((el) => !el.disabled && !el.closest(".dropdown, .multiselect"));

    const index = campos.indexOf(target);
    if (index === -1) return;

    event.preventDefault();

    const proximo = campos[index + 1];
    if (proximo) {
      proximo.focus();
    } else {
      form.requestSubmit();
    }
  }

  return { ref: formRef, onKeyDown: handleKeyDown };
}

export default useEnterToNextField;
