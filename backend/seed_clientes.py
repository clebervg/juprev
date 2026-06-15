"""
Gera 1000 clientes fake para o tenant do usuário clebervg@gmail.com.
Uso: python seed_clientes.py
"""

import random
import sqlite3
import uuid
from datetime import date, timedelta

TENANT_ID = "a330ca4ea57245b9a20ef1b9bda94034"
DB_PATH = "juprev.db"

# ── Dados para geração ──────────────────────────────────────────────────────

NOMES_MASC = [
    "Carlos", "José", "João", "Francisco", "Antonio", "Paulo", "Pedro",
    "Lucas", "Marcos", "Rafael", "Daniel", "Felipe", "Bruno", "Ricardo",
    "Eduardo", "Rodrigo", "Fernando", "Guilherme", "Henrique", "Alexandre",
    "Marcelo", "Diego", "Thiago", "André", "Leonardo", "Renato", "Fabio",
    "Leandro", "Cristiano", "Sérgio", "Vinícius", "Gabriel", "Matheus",
    "Roberto", "Cláudio", "Márcio", "Luís", "Fábio", "Wagner", "Adriano",
]

NOMES_FEM = [
    "Ana", "Maria", "Francisca", "Antônia", "Adriana", "Juliana", "Márcia",
    "Fernanda", "Patrícia", "Aline", "Sandra", "Camila", "Amanda", "Bruna",
    "Jéssica", "Letícia", "Luciana", "Vanessa", "Claudia", "Simone",
    "Beatriz", "Natália", "Débora", "Renata", "Viviane", "Carla", "Daniela",
    "Cristina", "Priscila", "Michele", "Larissa", "Isabela", "Tatiane",
    "Denise", "Vera", "Rosana", "Eliane", "Sueli", "Aparecida", "Regina",
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
    "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
    "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha",
    "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado",
    "Mendes", "Freitas", "Cardoso", "Ramos", "Gonçalves", "Santana", "Moura",
    "Araújo", "Cavalcanti", "Melo", "Teixeira", "Correia", "Pinto", "Azevedo",
    "Borges", "Castro", "Pinheiro", "Xavier", "Fonseca", "Cunha", "Monteiro",
]

CIDADES = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
    ("Salvador", "BA"), ("Fortaleza", "CE"), ("Curitiba", "PR"),
    ("Manaus", "AM"), ("Recife", "PE"), ("Porto Alegre", "RS"),
    ("Belém", "PA"), ("Goiânia", "GO"), ("Florianópolis", "SC"),
    ("São Luís", "MA"), ("Maceió", "AL"), ("Natal", "RN"),
    ("Teresina", "PI"), ("Campo Grande", "MS"), ("João Pessoa", "PB"),
    ("Aracaju", "SE"), ("Cuiabá", "MT"), ("Macapá", "AP"),
    ("Porto Velho", "RO"), ("Rio Branco", "AC"), ("Boa Vista", "RR"),
    ("Palmas", "TO"), ("Vitória", "ES"), ("Londrina", "PR"),
    ("Uberlândia", "MG"), ("Campinas", "SP"), ("São Bernardo do Campo", "SP"),
]

PROFISSOES = [
    "Agricultor", "Professor", "Motorista", "Pedreiro", "Carpinteiro",
    "Enfermeiro", "Comerciante", "Servidor Público", "Aposentado",
    "Trabalhador Rural", "Auxiliar Administrativo", "Técnico de Enfermagem",
    "Eletricista", "Mecânico", "Costureiro", "Doméstica", "Cuidador",
    "Segurança", "Auxiliar de Serviços Gerais", "Operador de Máquinas",
    "Padeiro", "Marceneiro", "Pintor", "Soldador", "Telefonista",
]

ESTADO_CIVIL = ["solteiro", "casado", "divorciado", "viuvo", "uniao_estavel"]
GENEROS = ["masculino", "feminino"]
ESCOLARIDADES = [
    "Fundamental incompleto", "Fundamental completo",
    "Médio incompleto", "Médio completo",
    "Superior incompleto", "Superior completo",
]


# ── Geração de CPF válido ───────────────────────────────────────────────────

def gerar_cpf() -> str:
    def calc_digito(digits: list[int], peso_inicial: int) -> int:
        total = sum(d * p for d, p in zip(digits, range(peso_inicial, 1, -1)))
        resto = (total * 10) % 11
        return 0 if resto >= 10 else resto

    base = [random.randint(0, 9) for _ in range(9)]
    d1 = calc_digito(base, 10)
    d2 = calc_digito(base + [d1], 11)
    return "".join(map(str, base + [d1, d2]))


def gerar_nis() -> str:
    """Gera NIS com dígito verificador válido."""
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    base = [random.randint(0, 9) for _ in range(10)]
    total = sum(d * p for d, p in zip(base, pesos))
    resto = total % 11
    check = 0 if resto < 2 else 11 - resto
    return "".join(map(str, base + [check]))


def data_nascimento_aleatoria(min_idade: int = 18, max_idade: int = 80) -> str:
    hoje = date.today()
    delta_days = (max_idade - min_idade) * 365
    nascimento = hoje - timedelta(days=min_idade * 365 + random.randint(0, delta_days))
    return nascimento.isoformat()


def telefone_aleatorio() -> str:
    ddd = random.choice(["11", "21", "31", "41", "51", "61", "71", "81", "85", "92"])
    numero = f"9{random.randint(10000000, 99999999)}"
    return f"{ddd}{numero}"


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cpfs_usados: set[str] = set()
    nis_usados: set[str] = set()

    # Carrega CPFs e NIS já existentes no tenant
    cur.execute("SELECT cpf FROM clients WHERE tenant_id = ?", (TENANT_ID,))
    cpfs_usados = {r[0] for r in cur.fetchall() if r[0]}
    cur.execute("SELECT nis FROM clients WHERE tenant_id = ?", (TENANT_ID,))
    nis_usados = {r[0] for r in cur.fetchall() if r[0]}

    inseridos = 0
    tentativas = 0
    MAX_TENTATIVAS = 5000

    print(f"Gerando 1000 clientes para tenant {TENANT_ID}...")

    while inseridos < 1000 and tentativas < MAX_TENTATIVAS:
        tentativas += 1
        genero = random.choice(GENEROS)
        nome_proprio = random.choice(NOMES_MASC if genero == "masculino" else NOMES_FEM)
        nome = f"{nome_proprio} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}"

        cpf = gerar_cpf()
        if cpf in cpfs_usados:
            continue
        cpfs_usados.add(cpf)

        # NIS opcional (~70% dos clientes têm NIS)
        nis = None
        if random.random() < 0.7:
            for _ in range(10):
                candidato = gerar_nis()
                if candidato not in nis_usados:
                    nis = candidato
                    nis_usados.add(nis)
                    break

        cidade, uf = random.choice(CIDADES)
        renda = round(random.uniform(1412, 12000), 2)
        tempo_contrib = random.randint(0, 35)

        row = (
            str(uuid.uuid4()).replace("-", ""),  # id
            TENANT_ID,
            nome,
            cpf,
            None,  # rg
            None,  # rg_orgao_expedidor
            data_nascimento_aleatoria(),
            None,  # nome_mae
            None,  # nome_pai
            random.choice(ESTADO_CIVIL),
            genero,
            nis,
            None,  # ctps_numero
            None,  # ctps_serie
            random.choice(ESCOLARIDADES),
            random.choice(PROFISSOES),
            None,  # email
            telefone_aleatorio(),
            1,     # whatsapp
            None,  # telefone_fixo
            None,  # contato_emergencia_nome
            None,  # contato_emergencia_telefone
            None,  # cep
            None,  # logradouro
            None,  # numero
            None,  # complemento
            None,  # bairro
            cidade,
            uf,
            None,  # tipo_residencia
            renda,
            0,     # possui_deficiencia
            None,  # tipo_deficiencia
            tempo_contrib,
            None,  # observacoes
        )

        try:
            cur.execute("""
                INSERT INTO clients (
                    id, tenant_id, nome, cpf, rg, rg_orgao_expedidor, data_nascimento,
                    nome_mae, nome_pai, estado_civil, genero, nis,
                    ctps_numero, ctps_serie, escolaridade, profissao,
                    email, telefone_celular, whatsapp, telefone_fixo,
                    contato_emergencia_nome, contato_emergencia_telefone,
                    cep, logradouro, numero, complemento, bairro, cidade, uf,
                    tipo_residencia, renda_mensal, possui_deficiencia,
                    tipo_deficiencia, tempo_contribuicao_anos, observacoes
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
            """, row)
            inseridos += 1
            if inseridos % 100 == 0:
                con.commit()
                print(f"  {inseridos}/1000 inseridos...")
        except sqlite3.IntegrityError:
            cpfs_usados.discard(cpf)
            if nis:
                nis_usados.discard(nis)

    con.commit()
    con.close()
    print(f"\nConcluído: {inseridos} clientes inseridos ({tentativas} tentativas).")


if __name__ == "__main__":
    main()
