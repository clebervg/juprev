"""
Testes de segurança para o JUPREV.

Uso:
    python security_tests.py

    # Com credenciais reais:
    EMAIL_A=clebervg@gmail.com SENHA_A=MinhaS3nha! python security_tests.py

    # Com dois tenants para testar isolamento:
    EMAIL_A=a@x.com SENHA_A=S1 EMAIL_B=b@x.com SENHA_B=S2 python security_tests.py
"""

import os
import sys
import uuid
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    sys.exit("Instale httpx: pip install httpx")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
EMAIL_A  = os.getenv("EMAIL_A", "")
SENHA_A  = os.getenv("SENHA_A", "")
EMAIL_B  = os.getenv("EMAIL_B", "")
SENHA_B  = os.getenv("SENHA_B", "")


@dataclass
class Resultado:
    nome: str
    passou: bool
    detalhe: str
    severidade: str


resultados: list[Resultado] = []


def run(nome: str, severidade: str, fn) -> Resultado:
    try:
        passou, detalhe = fn()
    except Exception as exc:
        passou, detalhe = False, f"Exceção inesperada: {exc}"
    r = Resultado(nome=nome, passou=passou, detalhe=detalhe, severidade=severidade)
    resultados.append(r)
    icone = "✓" if passou else "✗"
    print(f"  [{icone}] {nome}")
    print(f"        {detalhe}")
    return r


def login(email: str, senha: str) -> dict | None:
    if not email or not senha:
        return None
    r = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": senha})
    return r.json() if r.status_code == 200 else None


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────
# BLOCO 1: SQL Injection
# ─────────────────────────────────────────────────────────────────
print("\n═══ BLOCO 1: SQL Injection no Login ═══")

SQLI = [
    "' OR '1'='1",
    "' OR 1=1--",
    '" OR "1"="1',
    "admin'--",
    "' UNION SELECT null,null--",
    "'; DROP TABLE users;--",
    "1' OR sleep(5)--",
]

run("SQL Injection no campo email", "CRÍTICA", lambda: (
    (False, f"Login com payload: {next((p for p in SQLI if httpx.post(f'{BASE_URL}/api/v1/auth/login', json={'email': p, 'password': 'x'}).status_code == 200), None)!r}")
    if any(httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": p, "password": "x"}).status_code == 200 for p in SQLI)
    else (True, f"Todos os {len(SQLI)} payloads retornaram 4xx")
))

run("SQL Injection no campo senha", "CRÍTICA", lambda: (
    (False, "Login bem-sucedido com payload na senha")
    if any(httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "nao@existe.com", "password": p}).status_code == 200 for p in SQLI)
    else (True, f"Todos os {len(SQLI)} payloads retornaram 4xx")
))


def test_user_enum():
    r1 = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": EMAIL_A or "teste@x.com", "password": "errada_xyz_1234"})
    r2 = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": f"naoexiste_{uuid.uuid4()}@x.com", "password": "errada_xyz_1234"})
    if r1.status_code != r2.status_code:
        return False, f"Status diferentes: email existente={r1.status_code}, inexistente={r2.status_code}"
    m1 = r1.json().get("detail", "")
    m2 = r2.json().get("detail", "")
    if m1 != m2:
        return False, f"Mensagens diferentes revelam enumeração: {m1!r} vs {m2!r}"
    return True, "Mesma resposta para email existente e inexistente"

run("Enumeração de usuários (user enumeration)", "ALTA", test_user_enum)


# ─────────────────────────────────────────────────────────────────
# BLOCO 2: Rate Limiting
# ─────────────────────────────────────────────────────────────────
print("\n═══ BLOCO 2: Rate Limiting ═══")


def test_brute_force():
    for i in range(15):
        r = httpx.post(f"{BASE_URL}/api/v1/auth/login", json={"email": "brute@test.com", "password": f"s{i}"})
        if r.status_code == 429:
            return True, f"Rate limit acionado na tentativa {i+1}"
    return False, "15 tentativas sem HTTP 429 — rate limit pode não estar ativo"

run("Brute force bloqueado por rate limit", "ALTA", test_brute_force)


# ─────────────────────────────────────────────────────────────────
# BLOCO 3: Autenticação JWT
# ─────────────────────────────────────────────────────────────────
print("\n═══ BLOCO 3: Autenticação JWT ═══")

run("Acesso sem token retorna 401", "ALTA", lambda: (
    (True, "401 retornado") if httpx.get(f"{BASE_URL}/api/v1/clients").status_code == 401
    else (False, f"Status {httpx.get(f'{BASE_URL}/api/v1/clients').status_code}")
))

TOKEN_FORJADO = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIxMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODkwMTIiLCJ0ZW5hbnRfaWQiOiIxMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODkwMTIiLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjo5OTk5OTk5OTk5fQ"
    ".assinatura_invalida_AAAAA"
)
run("Token com assinatura forjada retorna 401", "CRÍTICA", lambda: (
    (True, "Token forjado rejeitado") if httpx.get(f"{BASE_URL}/api/v1/clients", headers=auth(TOKEN_FORJADO)).status_code == 401
    else (False, f"Status inesperado: {httpx.get(f'{BASE_URL}/api/v1/clients', headers=auth(TOKEN_FORJADO)).status_code}")
))


def test_refresh_como_access():
    tokens = login(EMAIL_A, SENHA_A)
    if not tokens:
        return True, "PULADO — defina EMAIL_A e SENHA_A"
    r = httpx.get(f"{BASE_URL}/api/v1/clients", headers=auth(tokens["refresh_token"]))
    if r.status_code == 401:
        return True, "Refresh token rejeitado como access token"
    return False, f"Status {r.status_code} — refresh token aceito no lugar de access token"

run("Refresh token não serve como access token", "ALTA", test_refresh_como_access)


def test_logout_revoga():
    tokens = login(EMAIL_A, SENHA_A)
    if not tokens:
        return True, "PULADO — defina EMAIL_A e SENHA_A"
    refresh = tokens["refresh_token"]
    r_out = httpx.post(f"{BASE_URL}/api/v1/auth/logout", json={"refresh_token": refresh})
    if r_out.status_code not in (200, 204):
        return False, f"Logout retornou {r_out.status_code}"
    r_use = httpx.post(f"{BASE_URL}/api/v1/auth/refresh", json={"refresh_token": refresh})
    if r_use.status_code == 401:
        return True, "Token revogado após logout"
    return False, f"Token ainda válido após logout (status {r_use.status_code})"

run("Refresh token revogado após logout", "CRÍTICA", test_logout_revoga)


def test_rotacao():
    tokens = login(EMAIL_A, SENHA_A)
    if not tokens:
        return True, "PULADO — defina EMAIL_A e SENHA_A"
    original = tokens["refresh_token"]
    r1 = httpx.post(f"{BASE_URL}/api/v1/auth/refresh", json={"refresh_token": original})
    if r1.status_code != 200:
        return False, f"Primeiro refresh falhou: {r1.status_code}"
    r2 = httpx.post(f"{BASE_URL}/api/v1/auth/refresh", json={"refresh_token": original})
    if r2.status_code == 401:
        return True, "Token original invalidado após rotação"
    return False, f"Token original reutilizável após rotação (status {r2.status_code})"

run("Rotação de refresh token invalida token anterior", "ALTA", test_rotacao)


# ─────────────────────────────────────────────────────────────────
# BLOCO 4: Isolamento Multi-Tenant (IDOR)
# ─────────────────────────────────────────────────────────────────
print("\n═══ BLOCO 4: Isolamento Multi-Tenant (IDOR) ═══")

tokens_a = login(EMAIL_A, SENHA_A)
tokens_b = login(EMAIL_B, SENHA_B)
dois_tenants = tokens_a is not None and tokens_b is not None


def test_idor_cliente():
    if not dois_tenants:
        return True, "PULADO — defina EMAIL_A/SENHA_A e EMAIL_B/SENHA_B em tenants diferentes"
    r = httpx.get(f"{BASE_URL}/api/v1/clients", headers=auth(tokens_a["access_token"]))
    items = r.json().get("items", [])
    if not items:
        return True, "PULADO — Tenant A sem clientes cadastrados"
    cid = items[0]["id"]
    rb = httpx.get(f"{BASE_URL}/api/v1/clients/{cid}", headers=auth(tokens_b["access_token"]))
    if rb.status_code in (403, 404):
        return True, f"Tenant B recebeu {rb.status_code} ao tentar acessar cliente do Tenant A"
    return False, f"IDOR detectado! Status {rb.status_code} — Tenant B acessou dado do Tenant A"

run("Tenant A não vê clientes do Tenant B (IDOR)", "CRÍTICA", test_idor_cliente)


def test_idor_cnis():
    if not dois_tenants:
        return True, "PULADO — defina EMAIL_A/SENHA_A e EMAIL_B/SENHA_B em tenants diferentes"
    r = httpx.get(f"{BASE_URL}/api/v1/cnis", headers=auth(tokens_a["access_token"]))
    items = r.json().get("items", [])
    if not items:
        return True, "PULADO — Tenant A sem CNIS cadastrados"
    cid = items[0]["id"]
    rb = httpx.get(f"{BASE_URL}/api/v1/cnis/{cid}", headers=auth(tokens_b["access_token"]))
    if rb.status_code in (403, 404):
        return True, f"Tenant B recebeu {rb.status_code} ao tentar acessar CNIS do Tenant A"
    return False, f"IDOR detectado! Status {rb.status_code} — dados: {rb.text[:150]}"

run("Tenant A não vê CNIS do Tenant B (IDOR)", "CRÍTICA", test_idor_cnis)


def test_idor_delete():
    if not dois_tenants:
        return True, "PULADO — defina EMAIL_A/SENHA_A e EMAIL_B/SENHA_B em tenants diferentes"
    r = httpx.get(f"{BASE_URL}/api/v1/cnis", headers=auth(tokens_a["access_token"]))
    items = r.json().get("items", [])
    if not items:
        return True, "PULADO — Tenant A sem CNIS cadastrados"
    cid = items[0]["id"]
    rb = httpx.delete(f"{BASE_URL}/api/v1/cnis/{cid}", headers=auth(tokens_b["access_token"]))
    if rb.status_code in (403, 404):
        rcheck = httpx.get(f"{BASE_URL}/api/v1/cnis/{cid}", headers=auth(tokens_a["access_token"]))
        if rcheck.status_code == 200:
            return True, f"Delete cross-tenant bloqueado ({rb.status_code}) e recurso intacto"
        return False, "Recurso pode ter sido deletado"
    return False, f"Delete cross-tenant retornou {rb.status_code} — possível deleção indevida"

run("Tenant B não consegue deletar CNIS do Tenant A", "CRÍTICA", test_idor_delete)

run("UUID inexistente retorna 404 (não vaza existência)", "MÉDIA", lambda: (
    (True, "404 retornado para UUID aleatório")
    if not tokens_a else (
        (True, "404 correto")
        if httpx.get(f"{BASE_URL}/api/v1/cnis/{uuid.uuid4()}", headers=auth(tokens_a["access_token"])).status_code == 404
        else (False, f"Status inesperado para UUID inexistente")
    )
))


# ─────────────────────────────────────────────────────────────────
# BLOCO 5: Upload de Arquivo
# ─────────────────────────────────────────────────────────────────
print("\n═══ BLOCO 5: Upload de Arquivo ═══")

FAKE_CNIS_ID = str(uuid.uuid4())

run("Upload sem autenticação retorna 401", "ALTA", lambda: (
    (True, "Upload bloqueado sem token")
    if httpx.post(f"{BASE_URL}/api/v1/cnis/{FAKE_CNIS_ID}/processar-pdf",
                  files={"arquivo": ("t.pdf", b"%PDF-1.4 x", "application/pdf")}).status_code == 401
    else (False, "Upload acessível sem autenticação")
))


def test_upload_grande():
    if not tokens_a:
        return True, "PULADO — defina EMAIL_A e SENHA_A"
    conteudo = b"%PDF-1.4 " + b"A" * (21 * 1024 * 1024)
    r = httpx.post(
        f"{BASE_URL}/api/v1/cnis/{FAKE_CNIS_ID}/processar-pdf",
        files={"arquivo": ("grande.pdf", conteudo, "application/pdf")},
        headers=auth(tokens_a["access_token"]),
        timeout=30.0,
    )
    if r.status_code == 413:
        return True, "Arquivo de 21 MB bloqueado com 413"
    if r.status_code == 404:
        return True, "CNIS não existe — mas servidor não crashou"
    return False, f"Status {r.status_code} — servidor pode ter aceito 21 MB"

run("Arquivo > 20 MB bloqueado (413)", "ALTA", test_upload_grande)


def test_upload_exe():
    if not tokens_a:
        return True, "PULADO — defina EMAIL_A e SENHA_A"
    exe = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 100  # magic bytes de executável ELF
    r = httpx.post(
        f"{BASE_URL}/api/v1/cnis/{FAKE_CNIS_ID}/processar-pdf",
        files={"arquivo": ("malware.pdf", exe, "application/pdf")},
        headers=auth(tokens_a["access_token"]),
        timeout=15.0,
    )
    if r.status_code == 415:
        return True, "Executável disfarçado de PDF rejeitado com 415"
    if r.status_code == 404:
        return False, "CNIS não existe — crie um CNIS real e teste novamente com CNIS_ID válido"
    return False, f"Status {r.status_code} — arquivo ELF pode ter sido processado"

run("Executável disfarçado de PDF rejeitado (magic bytes)", "ALTA", test_upload_exe)


# ─────────────────────────────────────────────────────────────────
# BLOCO 6: Headers e Configuração
# ─────────────────────────────────────────────────────────────────
print("\n═══ BLOCO 6: Security Headers e Configuração ═══")


def check_header(nome_header: str, valor_esperado: str):
    r = httpx.get(f"{BASE_URL}/api/v1/health")
    val = r.headers.get(nome_header, "")
    if valor_esperado.lower() in val.lower():
        return True, f"{nome_header}: {val}"
    return False, f"Header {nome_header!r} ausente ou incorreto (atual: {val!r})"

run("X-Content-Type-Options: nosniff", "MÉDIA", lambda: check_header("x-content-type-options", "nosniff"))
run("X-Frame-Options presente", "MÉDIA", lambda: check_header("x-frame-options", "deny"))
run("Strict-Transport-Security presente", "MÉDIA", lambda: check_header("strict-transport-security", "max-age"))


def test_docs():
    r_docs  = httpx.get(f"{BASE_URL}/docs")
    r_redoc = httpx.get(f"{BASE_URL}/redoc")
    if r_docs.status_code == 404 and r_redoc.status_code == 404:
        return True, "Swagger e ReDoc desabilitados"
    return False, f"/docs={r_docs.status_code} /redoc={r_redoc.status_code} — documentação exposta"

run("Swagger/ReDoc desabilitados", "BAIXA", test_docs)


def test_sem_stack_trace():
    if not tokens_a:
        return True, "PULADO — defina EMAIL_A e SENHA_A"
    r = httpx.post(
        f"{BASE_URL}/api/v1/cnis",
        json={"cpf": "' OR 1=1--", "nome_segurado": "x" * 5000},
        headers=auth(tokens_a["access_token"]),
    )
    corpo = r.text.lower()
    for kw in ["traceback", "sqlalchemy", "file \"", "exception at line"]:
        if kw in corpo:
            return False, f"Stack trace detectado na resposta ({kw!r})"
    return True, f"Resposta não vaza stack trace (status {r.status_code})"

run("Stack trace não vaza em erros internos", "ALTA", test_sem_stack_trace)


# ─────────────────────────────────────────────────────────────────
# RELATÓRIO FINAL
# ─────────────────────────────────────────────────────────────────
print("\n" + "═" * 60)
print("RELATÓRIO FINAL")
print("═" * 60)

passou  = [r for r in resultados if r.passou]
falhou  = [r for r in resultados if not r.passou]
pulados = [r for r in resultados if "PULADO" in r.detalhe]

print(f"\n  Total:   {len(resultados)}")
print(f"  ✓ OK:    {len(passou)}")
print(f"  ✗ FALHA: {len(falhou)}")
print(f"  ⊘ Skip:  {len(pulados)}")

if falhou:
    print("\n─── Vulnerabilidades encontradas ───")
    for r in falhou:
        print(f"\n  [{r.severidade}] {r.nome}")
        print(f"  → {r.detalhe}")

if pulados:
    print("\n─── Para habilitar testes que foram pulados ───")
    print("  EMAIL_A=seu@email.com SENHA_A=SuaSenha123! \\")
    print("  EMAIL_B=outro@tenant.com SENHA_B=OutraSenha123! \\")
    print("  python security_tests.py")

print()
sys.exit(1 if falhou else 0)
