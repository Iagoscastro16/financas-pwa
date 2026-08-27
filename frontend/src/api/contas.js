import client from "./client";

export async function listarContas({ includeInactive = false } = {}) {
  const response = await client.get("/contas", {
    params: { include_inactive: includeInactive },
  });
  return response.data;
}

export async function obterConta(contaId, { includeInactive = false } = {}) {
  const response = await client.get(`/contas/${contaId}`, {
    params: { include_inactive: includeInactive },
  });
  return response.data;
}

export async function criarConta({ nome, saldoInicial = 0 }) {
  const response = await client.post("/contas", { nome, saldo_inicial: saldoInicial });
  return response.data;
}

export async function atualizarConta(contaId, dados) {
  const response = await client.put(`/contas/${contaId}`, dados);
  return response.data;
}

export async function removerConta(contaId) {
  await client.delete(`/contas/${contaId}`);
}
