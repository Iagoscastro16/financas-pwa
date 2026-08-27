function normalizarData(data) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate());
}

function parseDataIso(dataIso) {
  // "YYYY-MM-DD" interpretado como data local (evita o bug clássico de
  // `new Date("YYYY-MM-DD")` ser lido como UTC e "voltar um dia" em fusos
  // horários negativos).
  return normalizarData(new Date(`${dataIso}T00:00:00`));
}

/**
 * Meses restantes de hoje até `prazoIso` ("YYYY-MM-DD"), arredondado para
 * cima (qualquer fração de mês conta como mais um mês inteiro) e com piso de
 * 1 (nunca zero/negativo, para não dividir por zero num prazo próximo).
 * Devolve `null` quando o prazo já passou.
 */
export function mesesRestantesAte(prazoIso) {
  const hoje = normalizarData(new Date());
  const prazo = parseDataIso(prazoIso);

  if (prazo < hoje) {
    return null;
  }

  const diffMeses =
    (prazo.getFullYear() - hoje.getFullYear()) * 12 + (prazo.getMonth() - hoje.getMonth());
  const comFracaoArredondada = prazo.getDate() > hoje.getDate() ? diffMeses + 1 : diffMeses;

  return Math.max(comFracaoArredondada, 1);
}

/**
 * Quanto precisa ser guardado por mês para atingir uma meta, dado seu estado
 * atual. Devolve um objeto com `status` discriminando os quatro casos
 * possíveis, para o componente decidir o que renderizar sem repetir essa
 * lógica de decisão:
 *
 * - "concluida": valor_atual já atingiu (ou passou) valor_alvo — independe
 *   do prazo, mesmo que ele já tenha vencido.
 * - "sem_prazo": meta sem prazo definido — não há como calcular um valor
 *   mensal (não é erro, só não é aplicável).
 * - "vencido": prazo já passou e a meta ainda não foi atingida.
 * - "ok": caso normal, com `valorNecessario` (por mês) e `meses` calculados.
 */
export function calcularNecessarioPorMes({ valor_atual: valorAtual, valor_alvo: valorAlvo, prazo }) {
  if (valorAtual >= valorAlvo) {
    return { status: "concluida" };
  }

  if (!prazo) {
    return { status: "sem_prazo" };
  }

  const meses = mesesRestantesAte(prazo);
  if (meses === null) {
    return { status: "vencido" };
  }

  return {
    status: "ok",
    meses,
    valorNecessario: (valorAlvo - valorAtual) / meses,
  };
}
