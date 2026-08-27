const MESES_PT = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

export function parseMesAno(mesAno) {
  const [ano, mes] = mesAno.split("-").map(Number);
  return { ano, mes };
}

export function formatarMesAno(ano, mes) {
  return `${String(ano).padStart(4, "0")}-${String(mes).padStart(2, "0")}`;
}

export function mesAtual() {
  const agora = new Date();
  return formatarMesAno(agora.getFullYear(), agora.getMonth() + 1);
}

export function somarMeses(mesAno, delta) {
  const { ano, mes } = parseMesAno(mesAno);
  const totalMeses = ano * 12 + (mes - 1) + delta;
  const novoAno = Math.floor(totalMeses / 12);
  const novoMes = (totalMeses % 12) + 1;
  return formatarMesAno(novoAno, novoMes);
}

export function nomeMesAno(mesAno) {
  const { ano, mes } = parseMesAno(mesAno);
  return `${MESES_PT[mes - 1]} ${ano}`;
}
