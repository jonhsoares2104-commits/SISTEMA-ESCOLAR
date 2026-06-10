from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from school_system.services import SchoolError, SchoolService


class SchoolServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.service = SchoolService(self.db_path)
        self.service.initialize()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_registers_student_teacher_class_and_enrollment(self) -> None:
        teacher_id = self.service.add_teacher("Ana Souza", "Matematica", "ana@escola.com")
        class_id = self.service.add_class("1A", 2026, teacher_id)
        student_id = self.service.add_student("Joao Silva", "2010-05-20")

        enrollment_id = self.service.enroll_student(student_id, class_id)

        enrollments = self.service.list_enrollments()
        self.assertEqual(enrollment_id, enrollments[0]["id"])
        self.assertEqual("Joao Silva", enrollments[0]["student"])
        self.assertEqual("1A", enrollments[0]["class_name"])

    def test_prevents_duplicate_enrollment(self) -> None:
        teacher_id = self.service.add_teacher("Ana Souza", "Matematica")
        class_id = self.service.add_class("1A", 2026, teacher_id)
        student_id = self.service.add_student("Joao Silva", "2010-05-20")

        self.service.enroll_student(student_id, class_id)

        with self.assertRaises(SchoolError):
            self.service.enroll_student(student_id, class_id)

    def test_grade_must_be_between_zero_and_ten(self) -> None:
        enrollment_id = self._create_enrollment()

        with self.assertRaises(SchoolError):
            self.service.add_grade(enrollment_id, "Matematica", 11)

    def test_builds_student_report(self) -> None:
        enrollment_id = self._create_enrollment()
        self.service.add_grade(enrollment_id, "Portugues", 9.0)
        self.service.add_attendance(enrollment_id, "2026-06-10", True)

        report = self.service.student_report(1)

        self.assertEqual("Joao Silva", report["student"]["name"])
        self.assertEqual(1, len(report["enrollments"]))
        self.assertEqual(1, len(report["grades"]))
        self.assertEqual(1, len(report["attendance"]))

    def _create_enrollment(self) -> int:
        teacher_id = self.service.add_teacher("Ana Souza", "Matematica")
        class_id = self.service.add_class("1A", 2026, teacher_id)
        student_id = self.service.add_student("Joao Silva", "2010-05-20")
        return self.service.enroll_student(student_id, class_id)


if __name__ == "__main__":
    unittest.main()

