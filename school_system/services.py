from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .database import init_db, managed_connection


class SchoolError(Exception):
    """Erro esperado de regra de negocio do sistema escolar."""


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[str, ...]


STUDENTS = Table("students", ("name", "birth_date", "email", "phone"))
TEACHERS = Table("teachers", ("name", "email", "subject"))
CLASSES = Table("classes", ("name", "year", "teacher_id"))


class SchoolService:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = db_path

    def initialize(self) -> None:
        init_db(self.db_path)

    def add_student(
        self, name: str, birth_date: str, email: str | None = None, phone: str | None = None
    ) -> int:
        self._validate_required("Nome do aluno", name)
        self._validate_date("Data de nascimento", birth_date)
        return self._insert(STUDENTS, {"name": name, "birth_date": birth_date, "email": email, "phone": phone})

    def list_students(self) -> list[sqlite3.Row]:
        return self._fetch_all("SELECT * FROM students ORDER BY name")

    def update_student(self, student_id: int, **fields: Any) -> None:
        self._update(STUDENTS, student_id, fields)

    def delete_student(self, student_id: int) -> None:
        self._delete("students", student_id)

    def add_teacher(self, name: str, subject: str, email: str | None = None) -> int:
        self._validate_required("Nome do professor", name)
        self._validate_required("Materia", subject)
        return self._insert(TEACHERS, {"name": name, "email": email, "subject": subject})

    def list_teachers(self) -> list[sqlite3.Row]:
        return self._fetch_all("SELECT * FROM teachers ORDER BY name")

    def update_teacher(self, teacher_id: int, **fields: Any) -> None:
        self._update(TEACHERS, teacher_id, fields)

    def delete_teacher(self, teacher_id: int) -> None:
        self._delete("teachers", teacher_id)

    def add_class(self, name: str, year: int, teacher_id: int | None = None) -> int:
        self._validate_required("Nome da turma", name)
        if year < 1900:
            raise SchoolError("Ano da turma invalido.")
        if teacher_id is not None:
            self._require_exists("teachers", teacher_id, "Professor nao encontrado.")
        return self._insert(CLASSES, {"name": name, "year": year, "teacher_id": teacher_id})

    def list_classes(self) -> list[sqlite3.Row]:
        return self._fetch_all(
            """
            SELECT classes.id, classes.name, classes.year, teachers.name AS teacher
            FROM classes
            LEFT JOIN teachers ON teachers.id = classes.teacher_id
            ORDER BY classes.year DESC, classes.name
            """
        )

    def update_class(self, class_id: int, **fields: Any) -> None:
        if fields.get("teacher_id") is not None:
            self._require_exists("teachers", int(fields["teacher_id"]), "Professor nao encontrado.")
        self._update(CLASSES, class_id, fields)

    def delete_class(self, class_id: int) -> None:
        self._delete("classes", class_id)

    def enroll_student(self, student_id: int, class_id: int, enrollment_date: str | None = None) -> int:
        self._require_exists("students", student_id, "Aluno nao encontrado.")
        self._require_exists("classes", class_id, "Turma nao encontrada.")
        if enrollment_date is not None:
            self._validate_date("Data de matricula", enrollment_date)

        query = """
            INSERT INTO enrollments (student_id, class_id, enrollment_date)
            VALUES (?, ?, COALESCE(?, CURRENT_DATE))
        """
        try:
            with managed_connection(self.db_path) as connection:
                cursor = connection.execute(query, (student_id, class_id, enrollment_date))
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise SchoolError("Aluno ja matriculado nesta turma.") from exc

    def list_enrollments(self) -> list[sqlite3.Row]:
        return self._fetch_all(
            """
            SELECT
                enrollments.id,
                students.name AS student,
                classes.name AS class_name,
                classes.year,
                enrollments.enrollment_date
            FROM enrollments
            JOIN students ON students.id = enrollments.student_id
            JOIN classes ON classes.id = enrollments.class_id
            ORDER BY classes.year DESC, classes.name, students.name
            """
        )

    def delete_enrollment(self, enrollment_id: int) -> None:
        self._delete("enrollments", enrollment_id)

    def add_grade(self, enrollment_id: int, subject: str, grade: float) -> int:
        self._require_exists("enrollments", enrollment_id, "Matricula nao encontrada.")
        self._validate_required("Materia", subject)
        if grade < 0 or grade > 10:
            raise SchoolError("Nota deve estar entre 0 e 10.")
        return self._insert(
            Table("grades", ("enrollment_id", "subject", "grade")),
            {"enrollment_id": enrollment_id, "subject": subject, "grade": grade},
        )

    def list_grades(self, enrollment_id: int | None = None) -> list[sqlite3.Row]:
        params: tuple[Any, ...] = ()
        where = ""
        if enrollment_id is not None:
            where = "WHERE grades.enrollment_id = ?"
            params = (enrollment_id,)
        return self._fetch_all(
            f"""
            SELECT grades.id, grades.enrollment_id, students.name AS student,
                   grades.subject, grades.grade, grades.created_at
            FROM grades
            JOIN enrollments ON enrollments.id = grades.enrollment_id
            JOIN students ON students.id = enrollments.student_id
            {where}
            ORDER BY grades.created_at DESC
            """,
            params,
        )

    def add_attendance(self, enrollment_id: int, attendance_date: str, present: bool) -> int:
        self._require_exists("enrollments", enrollment_id, "Matricula nao encontrada.")
        self._validate_date("Data de presenca", attendance_date)
        try:
            return self._insert(
                Table("attendance", ("enrollment_id", "date", "present")),
                {"enrollment_id": enrollment_id, "date": attendance_date, "present": int(present)},
            )
        except sqlite3.IntegrityError as exc:
            raise SchoolError("Ja existe registro de presenca para esta data.") from exc

    def list_attendance(self, enrollment_id: int | None = None) -> list[sqlite3.Row]:
        params: tuple[Any, ...] = ()
        where = ""
        if enrollment_id is not None:
            where = "WHERE attendance.enrollment_id = ?"
            params = (enrollment_id,)
        return self._fetch_all(
            f"""
            SELECT attendance.id, attendance.enrollment_id, students.name AS student,
                   attendance.date, attendance.present
            FROM attendance
            JOIN enrollments ON enrollments.id = attendance.enrollment_id
            JOIN students ON students.id = enrollments.student_id
            {where}
            ORDER BY attendance.date DESC
            """,
            params,
        )

    def student_report(self, student_id: int) -> dict[str, Any]:
        self._require_exists("students", student_id, "Aluno nao encontrado.")
        with managed_connection(self.db_path) as connection:
            student = connection.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
            enrollments = connection.execute(
                """
                SELECT enrollments.id, classes.name, classes.year, enrollments.enrollment_date
                FROM enrollments
                JOIN classes ON classes.id = enrollments.class_id
                WHERE enrollments.student_id = ?
                ORDER BY classes.year DESC, classes.name
                """,
                (student_id,),
            ).fetchall()

            enrollment_ids = [row["id"] for row in enrollments]
            if not enrollment_ids:
                return {"student": student, "enrollments": [], "grades": [], "attendance": []}

            placeholders = ",".join("?" for _ in enrollment_ids)
            grades = connection.execute(
                f"""
                SELECT enrollment_id, subject, grade, created_at
                FROM grades
                WHERE enrollment_id IN ({placeholders})
                ORDER BY subject, created_at
                """,
                enrollment_ids,
            ).fetchall()
            attendance = connection.execute(
                f"""
                SELECT enrollment_id, date, present
                FROM attendance
                WHERE enrollment_id IN ({placeholders})
                ORDER BY date DESC
                """,
                enrollment_ids,
            ).fetchall()

        return {
            "student": student,
            "enrollments": enrollments,
            "grades": grades,
            "attendance": attendance,
        }

    def _insert(self, table: Table, data: dict[str, Any]) -> int:
        columns = [column for column in table.columns if column in data]
        placeholders = ", ".join("?" for _ in columns)
        column_sql = ", ".join(columns)
        values = tuple(data[column] for column in columns)
        query = f"INSERT INTO {table.name} ({column_sql}) VALUES ({placeholders})"
        with managed_connection(self.db_path) as connection:
            cursor = connection.execute(query, values)
            return int(cursor.lastrowid)

    def _update(self, table: Table, row_id: int, fields: dict[str, Any]) -> None:
        allowed = {column: value for column, value in fields.items() if column in table.columns and value is not None}
        if not allowed:
            raise SchoolError("Nenhum campo valido para atualizar.")
        assignments = ", ".join(f"{column} = ?" for column in allowed)
        values = tuple(allowed.values()) + (row_id,)
        with managed_connection(self.db_path) as connection:
            cursor = connection.execute(f"UPDATE {table.name} SET {assignments} WHERE id = ?", values)
            if cursor.rowcount == 0:
                raise SchoolError("Registro nao encontrado.")

    def _delete(self, table_name: str, row_id: int) -> None:
        with managed_connection(self.db_path) as connection:
            cursor = connection.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))
            if cursor.rowcount == 0:
                raise SchoolError("Registro nao encontrado.")

    def _fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with managed_connection(self.db_path) as connection:
            return connection.execute(query, params).fetchall()

    def _require_exists(self, table_name: str, row_id: int, message: str) -> None:
        with managed_connection(self.db_path) as connection:
            result = connection.execute(f"SELECT 1 FROM {table_name} WHERE id = ?", (row_id,)).fetchone()
        if result is None:
            raise SchoolError(message)

    @staticmethod
    def _validate_required(label: str, value: str | None) -> None:
        if value is None or not value.strip():
            raise SchoolError(f"{label} e obrigatorio.")

    @staticmethod
    def _validate_date(label: str, value: str) -> None:
        try:
            datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise SchoolError(f"{label} deve estar no formato AAAA-MM-DD.") from exc
        if value > date.today().isoformat() and label == "Data de nascimento":
            raise SchoolError("Data de nascimento nao pode estar no futuro.")
