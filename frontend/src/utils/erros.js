export function extrairMensagemErro(err) {
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg).filter(Boolean).join(" ");
  }
  return "Não foi possível criar. Tente novamente.";
}
