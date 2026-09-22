import client from "./client";

export async function listarTransacoesRecorrentes({ includeInactive = false } = {}) {
  const response = await client.get("/transacoes-recorrentes", {
    params: { include_inactive: includeInactive },
  });
  return response.data;
}

export async function obterTransacaoRecorrente(recorrenciaId, { includeInactive = false } = {}) {
  const response = await client.get(`/transacoes-recorrentes/${recorrenciaId}`, {
    params: { include_inactive: includeInactive },
  });
  return response.data;
}

export async function criarTransacaoRecorrente({
  nome,
  valor,
  tipo,
  contaId,
  diaMes,
  dataInicio,
  dataFim = null,
  categoriaIds = [],
}) {
  const response = await client.post("/transacoes-recorrentes", {
    nome,
    valor,
    tipo,
    conta_id: contaId,
    dia_mes: diaMes,
    data_inicio: dataInicio,
    data_fim: dataFim,
    categoria_ids: categoriaIds,
  });
  return response.data;
}

export async function atualizarTransacaoRecorrente(recorrenciaId, dados) {
  const response = await client.put(`/transacoes-recorrentes/${recorrenciaId}`, dados);
  return response.data;
}

export async function cancelarTransacaoRecorrente(recorrenciaId) {
  await client.delete(`/transacoes-recorrentes/${recorrenciaId}`);
}
