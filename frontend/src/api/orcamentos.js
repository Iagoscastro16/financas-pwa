import client from "./client";

export async function listarOrcamentos({ mesAno } = {}) {
  const response = await client.get("/orcamentos", {
    params: mesAno ? { mes_ano: mesAno } : {},
  });
  return response.data;
}

export async function obterOrcamento(orcamentoId) {
  const response = await client.get(`/orcamentos/${orcamentoId}`);
  return response.data;
}

export async function criarOrcamento({ categoriaId, mesAno, valorMaximo }) {
  const response = await client.post("/orcamentos", {
    categoria_id: categoriaId,
    mes_ano: mesAno,
    valor_maximo: valorMaximo,
  });
  return response.data;
}

export async function atualizarOrcamento(orcamentoId, dados) {
  const response = await client.put(`/orcamentos/${orcamentoId}`, dados);
  return response.data;
}

export async function removerOrcamento(orcamentoId) {
  await client.delete(`/orcamentos/${orcamentoId}`);
}
