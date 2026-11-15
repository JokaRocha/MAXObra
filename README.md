# Obra Manager

Aplicação de gestão de obra em Python + Streamlit. O Supabase é o único armazenamento da aplicação; não existe fallback para base de dados SQL local.

## Requisitos

- Python 3.10+
- Windows, macOS ou Linux

## Configuração do Supabase

1. Aplique, pela ordem, as migrações em `supabase/migrations/` no SQL Editor do Supabase. Se as migrações iniciais já foram aplicadas, aplique também `20261115_secure_authenticated_access.sql`.
2. Publique a Edge Function `username-login` e configure `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` nos secrets da função. A chave `service_role` nunca deve ser colocada na app Streamlit.
3. Configure `SUPABASE_URL` e a chave publishable (`SUPABASE_KEY`) no ambiente local ou nos Secrets do Streamlit Community Cloud. O acesso às tabelas usa a sessão autenticada e RLS.

As políticas RLS restringem obras à conta autenticada; tarefas exigem role `manager` ou `builder`; movimentos financeiros exigem `manager`. A seleção da obra ativa é guardada apenas na sessão do navegador.

## Execução local

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

A aplicação abre em http://localhost:8501

## Funcionalidades

- Dashboard principal
- Menu de navegação
- Configuração da obra
- Dados remotos com Supabase e políticas RLS
- Interface adaptável a computador e telemóvel

Os dados que existam em ficheiros SQLite antigos não são importados automaticamente nem usados pela app.
