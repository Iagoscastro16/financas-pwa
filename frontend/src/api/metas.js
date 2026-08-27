import client from "./client";

export async function listarMetas() {
  const response = await client.get("/metas");
  return response.data;
}

export async function obterMeta(metaId) {
  const response = await client.get(`/metas/${metaId}`);
  return response.data;
}

export async function criarMeta({ nome, valorAlvo, valorAtual = 0, prazo = null }) {
  const response = await client.post("/metas", {
    nome,
    valor_alvo: valorAlvo,
    valor_atual: valorAtual,
    prazo,
  });
  return response.data;
}

export async function atualizarMeta(metaId, dados) {
  const response = await client.put(`/metas/${metaId}`, dados);
  return response.data;
}

export async function removerMeta(metaId) {
  await client.delete(`/metas/${metaId}`);
}
