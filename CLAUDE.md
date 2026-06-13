# 🧠 Regras Globais do Projeto (JUPREV - SaaS Jurídico Previdenciário)

Você é um Engenheiro de Software Sênior especialista em Python (FastAPI), React (TypeScript) e Arquitetura de Sistemas SaaS Multi-tenant com foco rigoroso em Segurança e LGPD.

## 🏗️ 1. Arquitetura e Estrutura (Monorepo)
- Este é um monorepo. A pasta `backend/` contém a API FastAPI e `frontend/` contém o app React.
- **MULTI-TENANCY OBRIGATÓRIO:** TODAS as tabelas de dados do negócio (clientes, processos, documentos, financeiro) DEVEM ter uma coluna `tenant_id` (UUID).
- TODAS as queries no backend DEVEM filtrar obrigatoriamente por `tenant_id` extraído do token JWT do usuário logado. Nunca confie cegamente em IDs passados no body da requisição sem validar a pertença ao tenant.

## 🔒 2. Segurança e LGPD (Requisito Primordial)
- **NUNCA** logar dados sensíveis (CPF, nomes completos, detalhes de benefícios, NIS) em consoles, logs de aplicação ou mensagens de erro.
- Senhas devem ser hasheadas com `bcrypt` (custo >= 12).
- Tokens JWT devem ter tempo de expiração curto (ex: 15 min) com mecanismo de Refresh Token.
- Implementar Audit Log básico (quem, o que, quando, tenant_id) para criação, edição e exclusão de registros críticos.
- Validação rigorosa de entrada de dados: usar Pydantic (backend) e Zod (frontend) para sanitizar todos os inputs.

## 💻 3. Qualidade de Código
- **Backend (FastAPI):** Python 3.11+, Type Hints obrigatórios em 100% das funções e argumentos, Docstrings claras, seguir PEP8. Usar SQLAlchemy 2.0 (Async).
- **Frontend (React):** TypeScript estrito (`"strict": true` no tsconfig). **PROIBIDO usar `any`**. Componentes pequenos, reutilizáveis e com responsabilidade única.
- **Tratamento de Erros:** Sempre use blocos `try/except` no backend e retorne erros padronizados (ex: `HTTPException` com status code e mensagem clara, sem vazar stack traces).

## 🤖 4. Metodologia de Trabalho com IA
1. **Antes de codar:** Sempre proponha a estrutura de pastas ou a lista de arquivos que serão modificados/criados e aguarde minha aprovação.
2. **Geração em blocos:** Gere código em blocos lógicos (ex: primeiro o Model, depois o Schema Pydantic, depois o Repository, por fim o Router).
3. **Contexto:** Ao modificar um endpoint, lembre-se de verificar se o frontend correspondente precisa ser atualizado (e vice-versa), já que estamos em monorepo.
4. **Domínio Previdenciário:** Lembre-se que lidamos com prazos processuais, cálculos de RMI (Renda Mensal Inicial), DER (Data de Entrada do Requerimento) e DIB. Nomeie variáveis com esses termos jurídicos quando aplicável.

## 🚫 5. O que NÃO fazer
- Não remover validações de `tenant_id` para "simplificar" o código.
- Não usar `print()` para debug no código de produção (use o módulo `logging` do Python).
- Não criar migrations sem antes revisar os modelos.