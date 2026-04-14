# Importador SQLite (Tkinter)

## O que faz?
- Cadastro simples de empresas (codigo e nome)
- Seleciona empresa
- Importa 3 planilhas (2 xlsx e 1 csv) e grava no SQLite
- Para cada importação: **substitui** os dados daquela empresa na tabela correspondente (DELETE + INSERT)

## Como rodar?
1. Crie e ative um venv (opcional, recomendado)
2. Instale dependências:
```bash
pip install pandas openpyxl
```
3. Execute:
```bash
python main.py
```

## Banco de dados
O arquivo `app.db` é criado na pasta do projeto.

Tabelas:
- `empresa(codigo TEXT PRIMARY KEY, nome TEXT NOT NULL)`
- Uma tabela para cada planilha:
  - `NCM E CEST`
  - `Estoque`
  - `notas`
Cada uma tem:
- `empresa_codigo TEXT NOT NULL`
- colunas da planilha (todas como TEXT, por enquanto)
