from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import Flask, flash, redirect, render_template, request, url_for

from school_system.services import SchoolError, SchoolService


app = Flask(__name__)
app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"

service = SchoolService()
service.initialize()

F = TypeVar("F", bound=Callable[..., object])


def handle_errors(view: F) -> F:
    @wraps(view)
    def wrapper(*args: object, **kwargs: object) -> object:
        try:
            return view(*args, **kwargs)
        except SchoolError as exc:
            flash(str(exc), "error")
            return redirect(request.referrer or url_for("index"))

    return wrapper  # type: ignore[return-value]


@app.get("/")
def index() -> str:
    students = service.list_students()
    teachers = service.list_teachers()
    classes = service.list_classes()
    enrollments = service.list_enrollments()
    grades = service.list_grades()
    attendance = service.list_attendance()

    average_grade = None
    if grades:
        average_grade = round(sum(float(row["grade"]) for row in grades) / len(grades), 2)

    attendance_rate = None
    if attendance:
        attendance_rate = round(
            sum(1 for row in attendance if row["present"]) / len(attendance) * 100,
            1,
        )

    return render_template(
        "index.html",
        students=students,
        teachers=teachers,
        classes=classes,
        enrollments=enrollments[:6],
        average_grade=average_grade,
        attendance_rate=attendance_rate,
    )


@app.route("/students", methods=["GET", "POST"])
@handle_errors
def students() -> object:
    if request.method == "POST":
        service.add_student(
            request.form["name"],
            request.form["birth_date"],
            request.form.get("email") or None,
            request.form.get("phone") or None,
        )
        flash("Aluno cadastrado com sucesso.", "success")
        return redirect(url_for("students"))

    return render_template("students.html", students=service.list_students())


@app.post("/students/<int:student_id>/delete")
@handle_errors
def delete_student(student_id: int) -> object:
    service.delete_student(student_id)
    flash("Aluno removido com sucesso.", "success")
    return redirect(url_for("students"))


@app.route("/teachers", methods=["GET", "POST"])
@handle_errors
def teachers() -> object:
    if request.method == "POST":
        service.add_teacher(
            request.form["name"],
            request.form["subject"],
            request.form.get("email") or None,
        )
        flash("Professor cadastrado com sucesso.", "success")
        return redirect(url_for("teachers"))

    return render_template("teachers.html", teachers=service.list_teachers())


@app.post("/teachers/<int:teacher_id>/delete")
@handle_errors
def delete_teacher(teacher_id: int) -> object:
    service.delete_teacher(teacher_id)
    flash("Professor removido com sucesso.", "success")
    return redirect(url_for("teachers"))


@app.route("/classes", methods=["GET", "POST"])
@handle_errors
def classes() -> object:
    if request.method == "POST":
        teacher_id = request.form.get("teacher_id")
        service.add_class(
            request.form["name"],
            int(request.form["year"]),
            int(teacher_id) if teacher_id else None,
        )
        flash("Turma cadastrada com sucesso.", "success")
        return redirect(url_for("classes"))

    return render_template(
        "classes.html",
        classes=service.list_classes(),
        teachers=service.list_teachers(),
    )


@app.post("/classes/<int:class_id>/delete")
@handle_errors
def delete_class(class_id: int) -> object:
    service.delete_class(class_id)
    flash("Turma removida com sucesso.", "success")
    return redirect(url_for("classes"))


@app.route("/enrollments", methods=["GET", "POST"])
@handle_errors
def enrollments() -> object:
    if request.method == "POST":
        service.enroll_student(
            int(request.form["student_id"]),
            int(request.form["class_id"]),
            request.form.get("date") or None,
        )
        flash("Matricula criada com sucesso.", "success")
        return redirect(url_for("enrollments"))

    return render_template(
        "enrollments.html",
        enrollments=service.list_enrollments(),
        students=service.list_students(),
        classes=service.list_classes(),
    )


@app.post("/enrollments/<int:enrollment_id>/delete")
@handle_errors
def delete_enrollment(enrollment_id: int) -> object:
    service.delete_enrollment(enrollment_id)
    flash("Matricula removida com sucesso.", "success")
    return redirect(url_for("enrollments"))


@app.route("/grades", methods=["GET", "POST"])
@handle_errors
def grades() -> object:
    if request.method == "POST":
        service.add_grade(
            int(request.form["enrollment_id"]),
            request.form["subject"],
            float(request.form["grade"]),
        )
        flash("Nota lancada com sucesso.", "success")
        return redirect(url_for("grades"))

    return render_template(
        "grades.html",
        grades=service.list_grades(),
        enrollments=service.list_enrollments(),
    )


@app.route("/attendance", methods=["GET", "POST"])
@handle_errors
def attendance() -> object:
    if request.method == "POST":
        service.add_attendance(
            int(request.form["enrollment_id"]),
            request.form["date"],
            request.form["present"] == "1",
        )
        flash("Frequencia registrada com sucesso.", "success")
        return redirect(url_for("attendance"))

    return render_template(
        "attendance.html",
        attendance=service.list_attendance(),
        enrollments=service.list_enrollments(),
    )


@app.route("/reports", methods=["GET", "POST"])
@handle_errors
def reports() -> object:
    report = None
    selected_student_id = None
    if request.method == "POST":
        selected_student_id = int(request.form["student_id"])
        report = service.student_report(selected_student_id)

    return render_template(
        "reports.html",
        students=service.list_students(),
        report=report,
        selected_student_id=selected_student_id,
    )


if __name__ == "__main__":
    app.run(debug=True)

