import client from "./client";

export async function listarCategorias({ includeInactive = false } = {}) {
  const response = await client.get("/categorias", {
    params: { include_inactive: includeInactive },
  });
  return response.data;
}

export async function obterCategoria(categoriaId, { includeInactive = false } = {}) {
  const response = await client.get(`/categorias/${categoriaId}`, {
    params: { include_inactive: includeInactive },
  });
  return response.data;
}

export async function criarCategoria({ nome, tipo }) {
  const response = await client.post("/categorias", { nome, tipo });
  return response.data;
}

export async function atualizarCategoria(categoriaId, dados) {
  const response = await client.put(`/categorias/${categoriaId}`, dados);
  return response.data;
}

export async function removerCategoria(categoriaId) {
  await client.delete(`/categorias/${categoriaId}`);
}
