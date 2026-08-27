import { useEffect, useState } from "react";

import { resumoCategorias, resumoMensal } from "../api/resumo";
import { mesAtual } from "../utils/mesAno";
import MonthSelector from "../components/MonthSelector/MonthSelector";
import BalanceCard from "../components/BalanceCard/BalanceCard";
import SummaryCard from "../components/SummaryCard/SummaryCard";
import CategoryPieChart from "../components/CategoryPieChart/CategoryPieChart";
import "./Dashboard.css";

export default function Dashboard() {
  const [selectedMonth, setSelectedMonth] = useState(mesAtual());
  const [mensal, setMensal] = useState(null);
  const [categorias, setCategorias] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);

    Promise.all([
      resumoMensal({ mesAno: selectedMonth }),
      resumoCategorias({ mesAno: selectedMonth }),
    ])
      .then(([dadosMensal, dadosCategorias]) => {
        if (cancelado) return;
        setMensal(dadosMensal);
        setCategorias(dadosCategorias);
      })
      .catch(() => {
        if (cancelado) return;
        setError("Não foi possível carregar os dados do resumo. Tente novamente.");
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, [selectedMonth]);

  return (
    <div className="dashboard">
      <MonthSelector value={selectedMonth} onChange={setSelectedMonth} />

      {error ? (
        <div className="card dashboard__error">{error}</div>
      ) : (
        <>
          <BalanceCard value={mensal?.saldo_total_contas} loading={loading} />
          <SummaryCard
            entradas={mensal?.total_entradas}
            saidas={mensal?.total_saidas}
            loading={loading}
          />
          <CategoryPieChart data={categorias} loading={loading} />
        </>
      )}
    </div>
  );
}
