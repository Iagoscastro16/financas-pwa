const formatterBRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function formatarMoeda(valor) {
  return formatterBRL.format(valor ?? 0);
}
