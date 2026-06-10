# Sistema Escolar em Python

Um sistema escolar simples feito em Python, com banco de dados SQLite e interface por linha de comando.

O projeto permite cadastrar alunos, professores, turmas, matrículas, notas e presenças. Ele foi pensado para ser fácil de estudar, modificar e publicar no GitHub.

## Funcionalidades

- Cadastro, listagem, atualização e remoção de alunos.
- Cadastro, listagem, atualização e remoção de professores.
- Criação e listagem de turmas.
- Matrícula de alunos em turmas.
- Lançamento e consulta de notas.
- Registro e consulta de frequência.
- Relatório completo por aluno.
- Testes automatizados com `unittest`.

## Requisitos

- Python 3.11 ou superior.

Não é necessário instalar dependências externas para usar o sistema.

## Como rodar

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/seu-usuario/sistema-escolar-python.git
cd sistema-escolar-python
```

Inicialize o banco de dados:

```bash
python -m school_system init-db
```

Cadastre um professor:

```bash
python -m school_system teachers add --name "Ana Souza" --email "ana@escola.com" --subject "Matematica"
```

Cadastre uma turma:

```bash
python -m school_system classes add --name "1A" --year 2026 --teacher-id 1
```

Cadastre um aluno:

```bash
python -m school_system students add --name "Joao Silva" --birth-date "2010-05-20" --email "joao@email.com" --phone "85999990000"
```

Matricule o aluno:

```bash
python -m school_system enrollments add --student-id 1 --class-id 1
```

Lance uma nota:

```bash
python -m school_system grades add --enrollment-id 1 --subject "Matematica" --grade 8.5
```

Registre presença:

```bash
python -m school_system attendance add --enrollment-id 1 --date "2026-06-10" --present yes
```

Veja o relatório do aluno:

```bash
python -m school_system report student --student-id 1
```

## Comandos úteis

```bash
python -m school_system students list
python -m school_system teachers list
python -m school_system classes list
python -m school_system enrollments list
python -m school_system grades list --enrollment-id 1
python -m school_system attendance list --enrollment-id 1
```

## Banco de dados

Por padrão, o sistema cria o arquivo `school.db` na pasta atual.

Você pode escolher outro caminho usando a variável de ambiente `SCHOOL_DB_PATH`:

```bash
SCHOOL_DB_PATH=meu_banco.db python -m school_system init-db
```

No PowerShell:

```powershell
$env:SCHOOL_DB_PATH = "meu_banco.db"
python -m school_system init-db
```

## Rodando os testes

```bash
python -m unittest
```

## Estrutura

```text
school_system/
  __main__.py
  cli.py
  database.py
  services.py
tests/
  test_services.py
```

## Sugestões de melhoria

- Criar interface web com Flask ou Django.
- Adicionar login de administrador, professor e aluno.
- Exportar relatórios em PDF ou CSV.
- Criar dashboard com indicadores da escola.
- Adicionar validação mais completa de CPF, telefone e e-mail.

