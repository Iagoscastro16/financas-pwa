import client from "./client";

export async function listarConfiguracoes() {
  const response = await client.get("/configuracao");
  return response.data;
}

export async function obterConfiguracao(chave) {
  const response = await client.get(`/configuracao/${chave}`);
  return response.data;
}

export async function atualizarConfiguracao(chave, valor) {
  const response = await client.put(`/configuracao/${chave}`, { valor });
  return response.data;
}
