"""
Motor de cálculo previdenciário.

Base legal:
- EC 103/2019 (Reforma da Previdência)
- Lei 8.213/91
- Decreto 3.048/99

Versão do algoritmo: 1.0.0
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import NamedTuple

from app.models.cnis import CNISRemuneracao

logger = logging.getLogger(__name__)

VERSAO_CALCULO = "1.0.0"

# Data da Reforma da Previdência (EC 103/2019)
DATA_REFORMA_EC103 = date(2019, 11, 13)

# Marco do Plano Real — competências anteriores a jul/1994 não entram no PBC
INICIO_PLANO_REAL = date(1994, 7, 1)

# Teto do INSS por ano (valores históricos resumidos para cálculos)
# Em produção, alimentar via tabela no banco. Aqui usamos os principais marcos.
TETO_INSS: dict[int, Decimal] = {
    1994: Decimal("859.17"),
    1999: Decimal("1255.32"),
    2003: Decimal("1869.34"),
    2008: Decimal("3038.99"),
    2012: Decimal("4159.00"),
    2015: Decimal("4663.75"),
    2019: Decimal("5839.45"),
    2020: Decimal("6101.06"),
    2021: Decimal("6433.57"),
    2022: Decimal("7087.22"),
    2023: Decimal("7786.02"),
    2024: Decimal("7786.02"),
    2025: Decimal("8157.41"),
}

# Alíquota de contribuição para cálculo do fator previdenciário
ALIQUOTA_CONTRIBUICAO = Decimal("0.31")

# Expectativa de sobrevida (em anos) — tabela IBGE simplificada
# Em produção, usar tabela completa. Aqui aproximação por faixa etária.
def _expectativa_sobrevida(idade: int) -> Decimal:
    tabela = {
        40: Decimal("40.4"), 45: Decimal("35.7"), 50: Decimal("31.1"),
        55: Decimal("26.8"), 60: Decimal("22.7"), 62: Decimal("21.0"),
        65: Decimal("18.8"), 67: Decimal("17.2"), 70: Decimal("14.7"),
        75: Decimal("11.1"), 80: Decimal("8.1"),
    }
    for faixa in sorted(tabela.keys(), reverse=True):
        if idade >= faixa:
            return tabela[faixa]
    return Decimal("45.0")


# ─── Tipos internos ───────────────────────────────────────────────────────────

@dataclass
class RequisitosBeneficio:
    tipo_beneficio: str
    data_der: date
    data_nascimento: date
    genero: str  # "masculino" | "feminino"
    tempo_contribuicao_dias: int
    tempo_especial_dias: int = 0
    grau_deficiencia: str | None = None  # "leve" | "moderada" | "grave"

    @property
    def idade_na_der(self) -> int:
        delta = self.data_der - self.data_nascimento
        return int(delta.days / 365.25)

    @property
    def tempo_contribuicao_anos(self) -> Decimal:
        return (Decimal(self.tempo_contribuicao_dias) / Decimal("365.25")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def tempo_especial_anos(self) -> Decimal:
        return (Decimal(self.tempo_especial_dias) / Decimal("365.25")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


@dataclass
class ResultadoCalculo:
    valido: bool
    salario_beneficio: Decimal
    coeficiente: Decimal
    fator_previdenciario: Decimal | None
    fator_acumulador: Decimal | None
    rmi_calculada: Decimal
    rmi_final: Decimal
    regra_aplicada: str
    requisitos_atendidos: dict
    detalhamento: dict
    alertas: list[str] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)


# ─── Teto do INSS ─────────────────────────────────────────────────────────────

def _teto_para_ano(ano: int) -> Decimal:
    for ref in sorted(TETO_INSS.keys(), reverse=True):
        if ano >= ref:
            return TETO_INSS[ref]
    return TETO_INSS[1994]


# ─── Salário de Benefício ─────────────────────────────────────────────────────

def calcular_salario_beneficio(
    remuneracoes: list[CNISRemuneracao],
    data_der: date,
    usar_80_porcento: bool = False,
) -> tuple[Decimal, list[dict]]:
    """
    Calcula o Salário de Benefício (SB).

    Regra pós-EC 103/2019: média simples de TODOS os salários desde 07/1994.
    Regra pré-reforma (quando usar_80_porcento=True): média dos 80% maiores desde 07/1994.

    Retorna (salario_beneficio, lista_de_salarios_utilizados).
    """
    validas = [
        r for r in remuneracoes
        if r.mes_referencia >= INICIO_PLANO_REAL
        and r.mes_referencia <= date(data_der.year, data_der.month, 1)
        and r.salario_valido
        and r.contribuiu_inss
    ]

    if not validas:
        return Decimal("0"), []

    # Usa salário corrigido se disponível, caso contrário usa o bruto
    salarios = [
        {
            "mes_referencia": str(r.mes_referencia),
            "salario_original": float(r.salario_contribuicao),
            "salario_utilizado": float(r.salario_contribuicao_corrigido or r.salario_contribuicao),
        }
        for r in sorted(validas, key=lambda x: x.mes_referencia)
    ]

    valores = sorted(
        [Decimal(str(s["salario_utilizado"])) for s in salarios],
        reverse=True,
    )

    if usar_80_porcento:
        qtd_80 = max(1, int(len(valores) * 0.8))
        valores_calc = valores[:qtd_80]
        metodo = "80% maiores salários (regra anterior à EC 103/2019)"
    else:
        valores_calc = valores
        metodo = "Média simples de todos os salários desde 07/1994 (regra pós-EC 103/2019)"

    media = sum(valores_calc) / Decimal(len(valores_calc))
    media = media.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    for s in salarios:
        s["incluido_no_calculo"] = s["salario_utilizado"] in [float(v) for v in valores_calc]

    logger.debug("SB calculado: %s (método: %s, n=%d)", media, metodo, len(valores_calc))
    return media, salarios


# ─── Fator Previdenciário ─────────────────────────────────────────────────────

def calcular_fator_previdenciario(
    tempo_contribuicao_anos: Decimal,
    idade: int,
    expectativa_sobrevida: Decimal | None = None,
) -> Decimal:
    """
    f = (TC/Es) × {1 + [(Id + TC × a) / 100]}
    TC = tempo de contribuição (anos)
    Es = expectativa de sobrevida na data da aposentadoria
    Id = idade
    a  = alíquota de contribuição (0.31)
    """
    es = expectativa_sobrevida or _expectativa_sobrevida(idade)
    tc = tempo_contribuicao_anos
    a = ALIQUOTA_CONTRIBUICAO
    id_ = Decimal(str(idade))

    fator = (tc / es) * (1 + (id_ + tc * a) / Decimal("100"))
    return fator.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


# ─── Verificação de Requisitos ────────────────────────────────────────────────

def verificar_requisitos(req: RequisitosBeneficio) -> tuple[bool, dict, list[str]]:
    """Verifica se os requisitos do benefício são atendidos na DER."""
    alertas: list[str] = []
    resultado: dict = {}

    tipo = req.tipo_beneficio
    idade = req.idade_na_der
    tc_anos = float(req.tempo_contribuicao_anos)
    tc_dias = req.tempo_contribuicao_dias
    genero = req.genero

    # Carência = 180 contribuições mensais (~15 anos) para aposentadorias
    carencia_meses = tc_dias // 30
    carencia_ok = carencia_meses >= 180

    if tipo in ("aposentadoria_idade_urbana",):
        idade_min = 65 if genero == "masculino" else 62
        tc_min = 15.0
        atende_idade = idade >= idade_min
        atende_tc = tc_anos >= tc_min
        atende_carencia = carencia_ok

        resultado = {
            "idade_minima": atende_idade,
            "idade_exigida": idade_min,
            "idade_atual": idade,
            "tempo_contribuicao_minimo": atende_tc,
            "tc_exigido_anos": tc_min,
            "tc_atual_anos": round(tc_anos, 2),
            "carencia": atende_carencia,
            "carencia_meses_atual": carencia_meses,
            "carencia_meses_exigida": 180,
        }
        atende = atende_idade and atende_tc and atende_carencia

        if not atende_idade:
            falta = idade_min - idade
            alertas.append(f"Faltam {falta} anos para atingir a idade mínima de {idade_min} anos.")
        if not atende_tc:
            falta_tc = tc_min - tc_anos
            alertas.append(f"Faltam {falta_tc:.1f} anos de contribuição (mínimo: {tc_min} anos).")

    elif tipo == "aposentadoria_tempo_contribuicao":
        # Regra de transição: pontos progressivos (EC 103/2019)
        pontos_atuais = idade + tc_anos
        pontos_necessarios = _pontos_necessarios(req.data_der, genero)
        tc_min = 35.0 if genero == "masculino" else 30.0
        atende_tc = tc_anos >= tc_min
        atende_pontos = pontos_atuais >= pontos_necessarios
        atende_carencia = carencia_ok

        resultado = {
            "pontos_atuais": round(pontos_atuais, 2),
            "pontos_necessarios": pontos_necessarios,
            "atende_pontos": atende_pontos,
            "tempo_contribuicao_minimo": atende_tc,
            "tc_exigido_anos": tc_min,
            "tc_atual_anos": round(tc_anos, 2),
            "carencia": atende_carencia,
        }
        atende = atende_tc and atende_pontos and atende_carencia

        if not atende_pontos:
            falta = pontos_necessarios - pontos_atuais
            alertas.append(
                f"Faltam {falta:.1f} pontos (soma idade+TC). Necessário: {pontos_necessarios}."
            )

    elif tipo in ("aposentadoria_especial_15", "aposentadoria_especial_20", "aposentadoria_especial_25"):
        anos_map = {"aposentadoria_especial_15": 15, "aposentadoria_especial_20": 20, "aposentadoria_especial_25": 25}
        te_min = anos_map[tipo]
        te_anos = float(req.tempo_especial_anos)
        atende_especial = te_anos >= te_min
        atende_carencia = carencia_ok

        resultado = {
            "tempo_especial_minimo": atende_especial,
            "te_exigido_anos": te_min,
            "te_atual_anos": round(te_anos, 2),
            "carencia": atende_carencia,
        }
        atende = atende_especial and atende_carencia

        if not atende_especial:
            falta = te_min - te_anos
            alertas.append(f"Faltam {falta:.1f} anos de tempo especial.")

    elif tipo in ("auxilio_doenca", "aposentadoria_invalidez"):
        carencia_12 = carencia_meses >= 12
        resultado = {
            "carencia": carencia_12,
            "carencia_meses_atual": carencia_meses,
            "carencia_meses_exigida": 12,
        }
        atende = carencia_12
        if not carencia_12:
            alertas.append(f"Carência insuficiente: {carencia_meses} meses (mínimo: 12).")

    elif tipo == "pensao_morte":
        # Sem carência para acidente; 18 meses para outros casos
        resultado = {"carencia": True}
        atende = True
        alertas.append("Verifique a qualidade de segurado e a causa do óbito para definir carência.")

    elif tipo == "salario_maternidade":
        carencia_meses_req = 10
        atende_carencia_mat = carencia_meses >= carencia_meses_req
        resultado = {
            "carencia": atende_carencia_mat,
            "carencia_meses_atual": carencia_meses,
            "carencia_meses_exigida": carencia_meses_req,
        }
        atende = atende_carencia_mat
        if not atende_carencia_mat:
            alertas.append(
                f"Carência insuficiente: {carencia_meses} meses (mínimo: {carencia_meses_req} para CI/MEI)."
            )

    else:
        resultado = {}
        atende = True
        alertas.append(f"Tipo de benefício '{tipo}' não tem validação de requisitos implementada.")

    return atende, resultado, alertas


def _pontos_necessarios(data_der: date, genero: str) -> float:
    """Tabela de pontos progressivos EC 103/2019."""
    ano = data_der.year

    if genero == "masculino":
        if ano <= 2019: return 96
        if ano == 2020: return 97
        if ano == 2021: return 98
        if ano == 2022: return 99
        if ano == 2023: return 100
        if ano == 2024: return 101
        if ano == 2025: return 102
        if ano == 2026: return 103
        return 105  # teto final
    else:
        if ano <= 2019: return 86
        if ano == 2020: return 87
        if ano == 2021: return 88
        if ano == 2022: return 89
        if ano == 2023: return 90
        if ano == 2024: return 91
        if ano == 2025: return 92
        if ano == 2026: return 93
        return 100  # teto final


# ─── Coeficiente de Cálculo ───────────────────────────────────────────────────

def calcular_coeficiente(
    tipo_beneficio: str,
    tempo_contribuicao_anos: Decimal,
    genero: str,
) -> Decimal:
    """
    Regra pós-EC 103/2019:
    - Base de 60%
    - +2% por ano que exceder 20 anos (homem) ou 15 anos (mulher) para aposentadoria por tempo
    - +2% por ano que exceder 20 anos para aposentadoria por idade
    Limitado a 100%.
    """
    tc = tempo_contribuicao_anos

    if tipo_beneficio in ("aposentadoria_idade_urbana", "aposentadoria_idade_rural"):
        base_anos = Decimal("20")
        excedente = max(Decimal("0"), tc - base_anos)
        coef = Decimal("0.60") + excedente * Decimal("0.02")

    elif tipo_beneficio == "aposentadoria_tempo_contribuicao":
        base_anos = Decimal("20") if genero == "masculino" else Decimal("15")
        excedente = max(Decimal("0"), tc - base_anos)
        coef = Decimal("0.60") + excedente * Decimal("0.02")

    elif tipo_beneficio in (
        "aposentadoria_especial_15", "aposentadoria_especial_20", "aposentadoria_especial_25",
        "aposentadoria_pcd_idade", "aposentadoria_pcd_tempo",
    ):
        coef = Decimal("1.00")

    elif tipo_beneficio in ("auxilio_doenca", "aposentadoria_invalidez"):
        coef = Decimal("0.91")  # Lei 8.213/91, art. 61

    elif tipo_beneficio == "pensao_morte":
        coef = Decimal("0.50")  # Cota base; dependentes somam +10% cada

    elif tipo_beneficio == "salario_maternidade":
        coef = Decimal("1.00")

    else:
        coef = Decimal("0.60")

    return min(coef, Decimal("1.00")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# ─── Cálculo Principal da RMI ─────────────────────────────────────────────────

def calcular_rmi(
    remuneracoes: list[CNISRemuneracao],
    req: RequisitosBeneficio,
    teto_na_der: Decimal | None = None,
) -> ResultadoCalculo:
    """
    Executa o cálculo completo da RMI com detalhamento passo a passo.
    """
    tipo = req.tipo_beneficio
    genero = req.genero
    tc_anos = req.tempo_contribuicao_anos
    idade = req.idade_na_der
    alertas: list[str] = []
    erros: list[str] = []

    # 1. Verifica requisitos
    atende_requisitos, requisitos, alertas_req = verificar_requisitos(req)
    alertas.extend(alertas_req)

    # 2. Salário de Benefício — regra pós-EC 103/2019
    sb, salarios_utilizados = calcular_salario_beneficio(remuneracoes, req.data_der)

    if sb == Decimal("0"):
        erros.append("Nenhuma remuneração válida encontrada para cálculo do salário de benefício.")
        return ResultadoCalculo(
            valido=False, salario_beneficio=Decimal("0"), coeficiente=Decimal("0"),
            fator_previdenciario=None, fator_acumulador=None,
            rmi_calculada=Decimal("0"), rmi_final=Decimal("0"),
            regra_aplicada="Cálculo inválido — sem remunerações",
            requisitos_atendidos=requisitos, detalhamento={},
            alertas=alertas, erros=erros,
        )

    # 3. Coeficiente
    coef = calcular_coeficiente(tipo, tc_anos, genero)

    # 4. Fator previdenciário (apenas para aposentadoria por tempo antes da reforma)
    fator_prev: Decimal | None = None
    fator_acumulador: Decimal | None = None

    if tipo == "aposentadoria_tempo_contribuicao" and req.data_der < DATA_REFORMA_EC103:
        fator_prev = calcular_fator_previdenciario(tc_anos, idade)
        rmi = sb * coef * fator_prev
        regra = "Fórmula com fator previdenciário (pré-EC 103/2019)"
    elif tipo == "aposentadoria_idade_urbana":
        # Pós-reforma: sem fator previdenciário
        rmi = sb * coef
        regra = "Regra permanente EC 103/2019 — aposentadoria por idade"
    else:
        rmi = sb * coef
        regra = f"Regra pós-EC 103/2019 — {tipo}"

    rmi = rmi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 5. Teto
    if teto_na_der is None:
        teto_na_der = _teto_para_ano(req.data_der.year)

    rmi_final = min(rmi, teto_na_der).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if rmi > teto_na_der:
        alertas.append(
            f"RMI calculada (R$ {rmi}) excede o teto do INSS (R$ {teto_na_der}). "
            f"Aplicado o teto de R$ {rmi_final}."
        )

    # 6. Comparativo pré-reforma (apenas se a DER for após a reforma)
    rmi_anterior: Decimal | None = None
    if req.data_der >= DATA_REFORMA_EC103 and tipo == "aposentadoria_tempo_contribuicao":
        sb_anterior, _ = calcular_salario_beneficio(remuneracoes, req.data_der, usar_80_porcento=True)
        fp_anterior = calcular_fator_previdenciario(tc_anos, idade)
        rmi_anterior = (sb_anterior * coef * fp_anterior).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if rmi_anterior > rmi:
            alertas.append(
                f"Regra anterior (com fator prev.) resultaria em RMI maior: R$ {rmi_anterior:.2f}. "
                "Considere a regra de transição mais favorável."
            )

    detalhamento = {
        "versao_calculo": VERSAO_CALCULO,
        "tipo_beneficio": tipo,
        "data_der": str(req.data_der),
        "genero": genero,
        "idade_na_der": idade,
        "tempo_contribuicao_anos": float(tc_anos),
        "total_salarios_analisados": len(salarios_utilizados),
        "salarios_utilizados": salarios_utilizados[:12],  # amostra (últimos 12)
        "salario_beneficio": float(sb),
        "coeficiente_aplicado": float(coef),
        "fator_previdenciario": float(fator_prev) if fator_prev else None,
        "rmi_calculada": float(rmi),
        "teto_inss": float(teto_na_der),
        "rmi_final": float(rmi_final),
        "passo_a_passo": [
            f"1. Salário de Benefício (SB) = R$ {sb:.2f}",
            f"2. Coeficiente = {float(coef) * 100:.2f}%",
            f"3. RMI = SB × coeficiente = R$ {float(sb):.2f} × {float(coef):.4f} = R$ {float(rmi):.2f}",
            f"4. Teto INSS ({req.data_der.year}) = R$ {float(teto_na_der):.2f}",
            f"5. RMI final (limitada ao teto) = R$ {float(rmi_final):.2f}",
        ],
    }

    if fator_prev:
        detalhamento["passo_a_passo"].insert(
            2, f"2b. Fator previdenciário = {float(fator_prev):.6f}"
        )
        detalhamento["passo_a_passo"][3] = (
            f"3. RMI = SB × coef × fator = R$ {float(sb):.2f} × {float(coef):.4f} × {float(fator_prev):.6f} = R$ {float(rmi):.2f}"
        )

    return ResultadoCalculo(
        valido=atende_requisitos and not erros,
        salario_beneficio=sb,
        coeficiente=coef,
        fator_previdenciario=fator_prev,
        fator_acumulador=fator_acumulador,
        rmi_calculada=rmi,
        rmi_final=rmi_final,
        regra_aplicada=regra,
        requisitos_atendidos=requisitos,
        detalhamento=detalhamento,
        alertas=alertas,
        erros=erros,
    )


# ─── Análise de Inconsistências do CNIS ──────────────────────────────────────

@dataclass
class Inconsistencia:
    tipo: str
    descricao: str
    periodo_afetado: str | None = None
    impacto_financeiro: Decimal | None = None
    recomendacao: str | None = None


def analisar_inconsistencias(
    remuneracoes: list[CNISRemuneracao],
    periodos: list,
) -> list[Inconsistencia]:
    """Identifica problemas no CNIS: sobreposição de vínculos, salários zerados, gaps, etc."""
    inconsistencias: list[Inconsistencia] = []

    # Salários zerados ou abaixo do mínimo
    for r in remuneracoes:
        if r.salario_contribuicao <= Decimal("0"):
            inconsistencias.append(Inconsistencia(
                tipo="salario_zerado",
                descricao=f"Salário zerado em {r.mes_referencia.strftime('%m/%Y')}.",
                periodo_afetado=str(r.mes_referencia),
                recomendacao="Verificar competência no extrato original do CNIS ou requerer retificação.",
            ))
        elif r.abaixo_minimo:
            inconsistencias.append(Inconsistencia(
                tipo="abaixo_salario_minimo",
                descricao=f"Salário abaixo do mínimo em {r.mes_referencia.strftime('%m/%Y')}: R$ {r.salario_contribuicao:.2f}.",
                periodo_afetado=str(r.mes_referencia),
                recomendacao="Competência pode não ser computada para carência. Verificar categoria.",
            ))

    # Períodos sobrepostos
    ativos = sorted([p for p in periodos if p.periodo_valido], key=lambda x: x.data_inicio)
    for i in range(len(ativos) - 1):
        a = ativos[i]
        b = ativos[i + 1]
        fim_a = a.data_fim or date.today()
        if fim_a >= b.data_inicio:
            inconsistencias.append(Inconsistencia(
                tipo="periodos_sobrepostos",
                descricao=(
                    f"Sobreposição entre vínculo {a.razao_social_empregador or a.cnpj_empregador} "
                    f"e {b.razao_social_empregador or b.cnpj_empregador}."
                ),
                periodo_afetado=f"{a.data_inicio} a {fim_a}",
                recomendacao="Períodos sobrepostos podem ser contados apenas uma vez. Verificar com INSS.",
            ))

    return inconsistencias
