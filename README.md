# Juprev — Sistema SaaS Jurídico Previdenciário

Monorepo com backend FastAPI e frontend React + Vite.

---

## Pré-requisitos

- Python 3.11+
- Node.js 22+ (use `nvm use 22`)
- Git

---

## Backend (FastAPI)

### 1. Ativar o ambiente virtual

```bash
source env/bin/activate
```

> Para sair do ambiente: `deactivate`

### 2. Instalar dependências

```bash
pip install -r backend/requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp backend/.env.example backend/.env
```

Edite o `backend/.env` conforme necessário. Para desenvolvimento local o SQLite já está configurado por padrão.

### 4. Rodar as migrações (Alembic)

```bash
cd backend

# Gerar a migration inicial a partir dos models
alembic revision --autogenerate -m "initial"

# Aplicar as migrations no banco
alembic upgrade head

cd ..
```

> Para criar novas migrations após alterar models: `alembic revision --autogenerate -m "descricao"`  
> Para reverter a última migration: `alembic downgrade -1`

### 5. Iniciar o servidor

```bash
cd backend
uvicorn app.main:app --reload
```

API disponível em: [http://localhost:8000](http://localhost:8000)  
Documentação interativa: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Frontend (React + Vite)

### 1. Garantir Node 22

```bash
nvm use 22
```

### 2. Instalar dependências

```bash
cd frontend
npm install
```

### 3. Iniciar o servidor de desenvolvimento

```bash
npm run dev
```

App disponível em: [http://localhost:5173](http://localhost:5173)

> O Vite faz proxy automático de `/api` para `http://localhost:8000`, então backend e frontend devem estar rodando ao mesmo tempo.

### 4. Gerar build de produção

```bash
npm run build
```

---

## Rodando tudo junto

Em dois terminais separados:

**Terminal 1 — Backend:**
```bash
source env/bin/activate
cd backend && uvicorn app.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
nvm use 22
cd frontend && npm run dev
```


## Testes
```bash
EMAIL_A=clebervg@gmail.com SENHA_A=SuaSenhaAqui \
EMAIL_B=outro@tenant.com  SENHA_B=OutraSenha \
python security_tests.py
```
---

## Estrutura do projeto

```
juprev/
├── env/                  # Ambiente virtual Python (não versionado)
├── backend/
│   ├── alembic/          # Migrações do banco de dados
│   ├── app/
│   │   ├── api/          # Routers e dependências (deps.py)
│   │   ├── core/         # Configurações, segurança, logging
│   │   ├── db/           # Engine, sessão e base dos models
│   │   ├── models/       # Models SQLAlchemy
│   │   ├── repositories/ # Acesso ao banco de dados
│   │   ├── schemas/      # Schemas Pydantic
│   │   ├── services/     # Lógica de negócio
│   │   └── main.py       # Entrypoint da API
│   ├── .env              # Variáveis de ambiente (não versionado)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/   # Layout e UI reutilizável
    │   ├── contexts/     # AuthContext (estado global)
    │   ├── pages/        # Login, Dashboard
    │   ├── router/       # AppRouter, ProtectedRoute
    │   ├── services/     # Axios (api.ts)
    │   ├── types/        # Interfaces TypeScript
    │   └── utils/        # storage.ts (tokens)
    └── package.json
```
