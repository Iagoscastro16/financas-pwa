import client from "./client";

export async function listarTransacoes({ mesAno, ordenarPor } = {}) {
  const params = {};
  if (mesAno) params.mes_ano = mesAno;
  if (ordenarPor) params.ordenar_por = ordenarPor;
  const response = await client.get("/transacoes", { params });
  return response.data;
}

export async function obterTransacao(transacaoId) {
  const response = await client.get(`/transacoes/${transacaoId}`);
  return response.data;
}

export async function criarTransacao({
  contaId,
  tipo,
  valor,
  data,
  descricao = null,
  categoriaIds = [],
}) {
  const response = await client.post("/transacoes", {
    conta_id: contaId,
    tipo,
    valor,
    data,
    descricao,
    categoria_ids: categoriaIds,
  });
  return response.data;
}

export async function atualizarTransacao(transacaoId, dados) {
  const response = await client.put(`/transacoes/${transacaoId}`, dados);
  return response.data;
}

export async function removerTransacao(transacaoId) {
  await client.delete(`/transacoes/${transacaoId}`);
}
