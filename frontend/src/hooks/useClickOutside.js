import { useEffect, useRef } from "react";

/**
 * Chama `onOutside` quando o usuário clica fora do elemento referenciado por
 * `ref`, ou pressiona Escape. `onOutside` é lido de uma ref interna a cada
 * chamada, então pode ser passada como uma arrow function inline sem
 * recriar os listeners a cada render.
 */
export function useClickOutside(ref, onOutside) {
  const callbackRef = useRef(onOutside);
  useEffect(() => {
    callbackRef.current = onOutside;
  });

  useEffect(() => {
    function handlePointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) {
        callbackRef.current();
      }
    }
    function handleKeyDown(event) {
      if (event.key === "Escape") {
        callbackRef.current();
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [ref]);
}

export default useClickOutside;
