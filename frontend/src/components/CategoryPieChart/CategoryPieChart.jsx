import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatarMoeda } from "../../utils/format";
import "./CategoryPieChart.css";

// Paleta desaturada feita sob medida para o tema escuro: tons de
// saturação/luminosidade moderadas espalhados pelo círculo cromático,
// evitando deliberadamente as cores semânticas já usadas em outros
// pontos da UI (vermelho de saída, teal de entrada, laranja de aviso).
// Cores primárias saturadas tendem a "gritar" sobre um fundo escuro;
// tons acinzentados/pastel mantêm várias fatias legíveis ao mesmo tempo
// sem competir com o significado que essas cores semânticas já carregam
// em outros componentes (BalanceCard, SummaryCard).
const PALETTE = [
  "#7C9CBF", // azul acinzentado
  "#B08BC9", // lilás
  "#C9A05C", // dourado queimado
  "#7FB59E", // verde salvia
  "#C97F9E", // rosa antigo
  "#8FA85C", // verde oliva
  "#6FB8C9", // ciano suave
  "#A69CB0", // cinza lavanda
];

export default function CategoryPieChart({ data, loading }) {
  if (loading) {
    return (
      <div className="card category-pie">
        <h2 className="category-pie__title">Gastos por categoria</h2>
        <div className="skeleton category-pie__skeleton" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="card category-pie">
        <h2 className="category-pie__title">Gastos por categoria</h2>
        <p className="category-pie__empty">Nenhum gasto registrado neste mês.</p>
      </div>
    );
  }

  return (
    <div className="card category-pie">
      <h2 className="category-pie__title">Gastos por categoria</h2>
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
            data={data}
            dataKey="total"
            nameKey="nome"
            cx="50%"
            cy="50%"
            outerRadius={110}
            label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
          >
            {data.map((entry, index) => (
              <Cell key={entry.categoria_id ?? "sem-categoria"} fill={PALETTE[index % PALETTE.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, name) => [formatarMoeda(value), name]}
            contentStyle={{
              backgroundColor: "var(--color-bg)",
              border: "1px solid var(--color-text-secondary)",
              borderRadius: 8,
            }}
            itemStyle={{ color: "var(--color-text-primary)" }}
            labelStyle={{ color: "var(--color-text-primary)" }}
          />
          <Legend wrapperStyle={{ color: "var(--color-text-secondary)" }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
