from pydantic import BaseModel


class ResumoMensal(BaseModel):
    mes_ano: str
    total_entradas: float
    total_saidas: float
    saldo_periodo: float
    saldo_total_contas: float


class ResumoCategoria(BaseModel):
    categoria_id: int | None
    nome: str
    total: float
    percentual: float


class VariacaoPercentual(BaseModel):
    # None quando o mês-base é zero: variação percentual não é calculável
    # a partir de uma base zero (diferente de 0%, que significaria "sem
    # mudança").
    total_entradas: float | None
    total_saidas: float | None


class ResumoComparativo(BaseModel):
    mes1: ResumoMensal
    mes2: ResumoMensal
    variacao_percentual: VariacaoPercentual
