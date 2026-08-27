from datetime import date, datetime

from fastapi import HTTPException, status


def limites_mes(mes_ano: str) -> tuple[date, date]:
    """Converte "YYYY-MM" no intervalo [inicio, fim) do mês (fim exclusivo,
    primeiro dia do mês seguinte). Compartilhado entre app.routers.resumo e
    app.routers.transacoes para manter a mesma validação de mes_ano."""
    try:
        inicio = datetime.strptime(mes_ano, "%Y-%m").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="mes_ano deve estar no formato YYYY-MM"
        )
    if inicio.month == 12:
        fim = date(inicio.year + 1, 1, 1)
    else:
        fim = date(inicio.year, inicio.month + 1, 1)
    return inicio, fim
