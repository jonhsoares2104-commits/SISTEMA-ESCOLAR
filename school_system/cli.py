from __future__ import annotations

import argparse
import sqlite3
import sys
from typing import Any, Iterable

from .services import SchoolError, SchoolService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sistema escolar em Python")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-db", help="Inicializa o banco de dados")
    init_parser.set_defaults(handler=handle_init_db)

    students = subparsers.add_parser("students", help="Gerencia alunos")
    build_students_parser(students)

    teachers = subparsers.add_parser("teachers", help="Gerencia professores")
    build_teachers_parser(teachers)

    classes = subparsers.add_parser("classes", help="Gerencia turmas")
    build_classes_parser(classes)

    enrollments = subparsers.add_parser("enrollments", help="Gerencia matriculas")
    build_enrollments_parser(enrollments)

    grades = subparsers.add_parser("grades", help="Gerencia notas")
    build_grades_parser(grades)

    attendance = subparsers.add_parser("attendance", help="Gerencia frequencia")
    build_attendance_parser(attendance)

    report = subparsers.add_parser("report", help="Relatorios")
    build_report_parser(report)

    return parser


def build_students_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    add = subparsers.add_parser("add", help="Cadastra aluno")
    add.add_argument("--name", required=True)
    add.add_argument("--birth-date", required=True)
    add.add_argument("--email")
    add.add_argument("--phone")
    add.set_defaults(handler=handle_student_add)

    subparsers.add_parser("list", help="Lista alunos").set_defaults(handler=handle_student_list)

    update = subparsers.add_parser("update", help="Atualiza aluno")
    update.add_argument("--id", required=True, type=int)
    update.add_argument("--name")
    update.add_argument("--birth-date")
    update.add_argument("--email")
    update.add_argument("--phone")
    update.set_defaults(handler=handle_student_update)

    delete = subparsers.add_parser("delete", help="Remove aluno")
    delete.add_argument("--id", required=True, type=int)
    delete.set_defaults(handler=handle_student_delete)


def build_teachers_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    add = subparsers.add_parser("add", help="Cadastra professor")
    add.add_argument("--name", required=True)
    add.add_argument("--subject", required=True)
    add.add_argument("--email")
    add.set_defaults(handler=handle_teacher_add)

    subparsers.add_parser("list", help="Lista professores").set_defaults(handler=handle_teacher_list)

    update = subparsers.add_parser("update", help="Atualiza professor")
    update.add_argument("--id", required=True, type=int)
    update.add_argument("--name")
    update.add_argument("--subject")
    update.add_argument("--email")
    update.set_defaults(handler=handle_teacher_update)

    delete = subparsers.add_parser("delete", help="Remove professor")
    delete.add_argument("--id", required=True, type=int)
    delete.set_defaults(handler=handle_teacher_delete)


def build_classes_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    add = subparsers.add_parser("add", help="Cadastra turma")
    add.add_argument("--name", required=True)
    add.add_argument("--year", required=True, type=int)
    add.add_argument("--teacher-id", type=int)
    add.set_defaults(handler=handle_class_add)

    subparsers.add_parser("list", help="Lista turmas").set_defaults(handler=handle_class_list)

    update = subparsers.add_parser("update", help="Atualiza turma")
    update.add_argument("--id", required=True, type=int)
    update.add_argument("--name")
    update.add_argument("--year", type=int)
    update.add_argument("--teacher-id", type=int)
    update.set_defaults(handler=handle_class_update)

    delete = subparsers.add_parser("delete", help="Remove turma")
    delete.add_argument("--id", required=True, type=int)
    delete.set_defaults(handler=handle_class_delete)


def build_enrollments_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    add = subparsers.add_parser("add", help="Matricula aluno em turma")
    add.add_argument("--student-id", required=True, type=int)
    add.add_argument("--class-id", required=True, type=int)
    add.add_argument("--date")
    add.set_defaults(handler=handle_enrollment_add)

    subparsers.add_parser("list", help="Lista matriculas").set_defaults(handler=handle_enrollment_list)

    delete = subparsers.add_parser("delete", help="Remove matricula")
    delete.add_argument("--id", required=True, type=int)
    delete.set_defaults(handler=handle_enrollment_delete)


def build_grades_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    add = subparsers.add_parser("add", help="Lanca nota")
    add.add_argument("--enrollment-id", required=True, type=int)
    add.add_argument("--subject", required=True)
    add.add_argument("--grade", required=True, type=float)
    add.set_defaults(handler=handle_grade_add)

    list_parser = subparsers.add_parser("list", help="Lista notas")
    list_parser.add_argument("--enrollment-id", type=int)
    list_parser.set_defaults(handler=handle_grade_list)


def build_attendance_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    add = subparsers.add_parser("add", help="Registra presenca")
    add.add_argument("--enrollment-id", required=True, type=int)
    add.add_argument("--date", required=True)
    add.add_argument("--present", required=True, choices=("yes", "no", "sim", "nao"))
    add.set_defaults(handler=handle_attendance_add)

    list_parser = subparsers.add_parser("list", help="Lista frequencia")
    list_parser.add_argument("--enrollment-id", type=int)
    list_parser.set_defaults(handler=handle_attendance_list)


def build_report_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers(dest="action", required=True)

    student = subparsers.add_parser("student", help="Relatorio por aluno")
    student.add_argument("--student-id", required=True, type=int)
    student.set_defaults(handler=handle_student_report)


def handle_init_db(service: SchoolService, _args: argparse.Namespace) -> None:
    service.initialize()
    print("Banco de dados inicializado com sucesso.")


def handle_student_add(service: SchoolService, args: argparse.Namespace) -> None:
    new_id = service.add_student(args.name, args.birth_date, args.email, args.phone)
    print(f"Aluno cadastrado com ID {new_id}.")


def handle_student_list(service: SchoolService, _args: argparse.Namespace) -> None:
    print_table(service.list_students(), ("id", "name", "birth_date", "email", "phone"))


def handle_student_update(service: SchoolService, args: argparse.Namespace) -> None:
    service.update_student(
        args.id,
        name=args.name,
        birth_date=args.birth_date,
        email=args.email,
        phone=args.phone,
    )
    print("Aluno atualizado com sucesso.")


def handle_student_delete(service: SchoolService, args: argparse.Namespace) -> None:
    service.delete_student(args.id)
    print("Aluno removido com sucesso.")


def handle_teacher_add(service: SchoolService, args: argparse.Namespace) -> None:
    new_id = service.add_teacher(args.name, args.subject, args.email)
    print(f"Professor cadastrado com ID {new_id}.")


def handle_teacher_list(service: SchoolService, _args: argparse.Namespace) -> None:
    print_table(service.list_teachers(), ("id", "name", "email", "subject"))


def handle_teacher_update(service: SchoolService, args: argparse.Namespace) -> None:
    service.update_teacher(args.id, name=args.name, subject=args.subject, email=args.email)
    print("Professor atualizado com sucesso.")


def handle_teacher_delete(service: SchoolService, args: argparse.Namespace) -> None:
    service.delete_teacher(args.id)
    print("Professor removido com sucesso.")


def handle_class_add(service: SchoolService, args: argparse.Namespace) -> None:
    new_id = service.add_class(args.name, args.year, args.teacher_id)
    print(f"Turma cadastrada com ID {new_id}.")


def handle_class_list(service: SchoolService, _args: argparse.Namespace) -> None:
    print_table(service.list_classes(), ("id", "name", "year", "teacher"))


def handle_class_update(service: SchoolService, args: argparse.Namespace) -> None:
    service.update_class(args.id, name=args.name, year=args.year, teacher_id=args.teacher_id)
    print("Turma atualizada com sucesso.")


def handle_class_delete(service: SchoolService, args: argparse.Namespace) -> None:
    service.delete_class(args.id)
    print("Turma removida com sucesso.")


def handle_enrollment_add(service: SchoolService, args: argparse.Namespace) -> None:
    new_id = service.enroll_student(args.student_id, args.class_id, args.date)
    print(f"Matricula criada com ID {new_id}.")


def handle_enrollment_list(service: SchoolService, _args: argparse.Namespace) -> None:
    print_table(service.list_enrollments(), ("id", "student", "class_name", "year", "enrollment_date"))


def handle_enrollment_delete(service: SchoolService, args: argparse.Namespace) -> None:
    service.delete_enrollment(args.id)
    print("Matricula removida com sucesso.")


def handle_grade_add(service: SchoolService, args: argparse.Namespace) -> None:
    new_id = service.add_grade(args.enrollment_id, args.subject, args.grade)
    print(f"Nota lancada com ID {new_id}.")


def handle_grade_list(service: SchoolService, args: argparse.Namespace) -> None:
    print_table(
        service.list_grades(args.enrollment_id),
        ("id", "enrollment_id", "student", "subject", "grade", "created_at"),
    )


def handle_attendance_add(service: SchoolService, args: argparse.Namespace) -> None:
    present = args.present in {"yes", "sim"}
    new_id = service.add_attendance(args.enrollment_id, args.date, present)
    print(f"Presenca registrada com ID {new_id}.")


def handle_attendance_list(service: SchoolService, args: argparse.Namespace) -> None:
    rows = [
        {**dict(row), "present": "sim" if row["present"] else "nao"}
        for row in service.list_attendance(args.enrollment_id)
    ]
    print_table(rows, ("id", "enrollment_id", "student", "date", "present"))


def handle_student_report(service: SchoolService, args: argparse.Namespace) -> None:
    report = service.student_report(args.student_id)
    student = report["student"]
    print(f"Aluno: {student['name']} (ID {student['id']})")
    print(f"Nascimento: {student['birth_date']}")
    print(f"Email: {student['email'] or '-'}")
    print(f"Telefone: {student['phone'] or '-'}")
    print()

    print("Matriculas:")
    print_table(report["enrollments"], ("id", "name", "year", "enrollment_date"))
    print()

    print("Notas:")
    print_table(report["grades"], ("enrollment_id", "subject", "grade", "created_at"))
    print()

    print("Frequencia:")
    attendance_rows = [
        {**dict(row), "present": "sim" if row["present"] else "nao"}
        for row in report["attendance"]
    ]
    print_table(attendance_rows, ("enrollment_id", "date", "present"))


def print_table(rows: Iterable[Any], columns: tuple[str, ...]) -> None:
    normalized = [dict(row) for row in rows]
    if not normalized:
        print("Nenhum registro encontrado.")
        return

    widths = {
        column: max(len(column), *(len(format_value(row.get(column))) for row in normalized))
        for column in columns
    }
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)
    print(header)
    print(separator)
    for row in normalized:
        print(" | ".join(format_value(row.get(column)).ljust(widths[column]) for column in columns))


def format_value(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = SchoolService()

    try:
        args.handler(service, args)
    except SchoolError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    except sqlite3.OperationalError as exc:
        print(f"Erro no banco de dados: {exc}", file=sys.stderr)
        print("Dica: rode `python -m school_system init-db` antes de usar o sistema.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
