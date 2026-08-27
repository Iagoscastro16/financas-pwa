import client from "./client";

export async function resumoMensal({ mesAno } = {}) {
  const response = await client.get("/resumo/mensal", {
    params: mesAno ? { mes_ano: mesAno } : {},
  });
  return response.data;
}

export async function resumoCategorias({ mesAno } = {}) {
  const response = await client.get("/resumo/categorias", {
    params: mesAno ? { mes_ano: mesAno } : {},
  });
  return response.data;
}

export async function resumoCategoriasTotal() {
  const response = await client.get("/resumo/categorias/total");
  return response.data;
}

export async function resumoComparativo(mes1, mes2) {
  const response = await client.get("/resumo/comparativo", {
    params: { mes1, mes2 },
  });
  return response.data;
}
