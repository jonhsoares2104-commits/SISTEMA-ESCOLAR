from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import app
from school_system.services import SchoolService


class WebAppTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "web-test.db"
        app.service = SchoolService(self.db_path)
        app.service.initialize()
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_home_loads(self) -> None:
        response = self.client.get("/")

        self.assertEqual(200, response.status_code)
        self.assertIn("Resumo da escola", response.get_data(as_text=True))

    def test_creates_student_from_web_form(self) -> None:
        response = self.client.post(
            "/students",
            data={
                "name": "Maria Lima",
                "birth_date": "2011-03-14",
                "email": "maria@email.com",
                "phone": "85988887777",
            },
            follow_redirects=True,
        )

        page = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("Aluno cadastrado com sucesso.", page)
        self.assertIn("Maria Lima", page)


if __name__ == "__main__":
    unittest.main()

