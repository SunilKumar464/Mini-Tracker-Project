from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from tracker.models import Project, Task


class ProjectTaskTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass456")

    # 1. Duplicate project name should fail
    def test_duplicate_project_name_not_allowed(self):
        Project.objects.create(name="My Project", owner=self.user1)
        duplicate = Project(name="My Project", owner=self.user1)

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    # 2. Task marked done with future due date should fail
    def test_done_task_with_future_date_invalid(self):
        project = Project.objects.create(name="Test Project", owner=self.user1)
        future_date = timezone.now().date() + timedelta(days=5)

        task = Task(
            project=project,
            title="Invalid Task",
            status="done",
            due_date=future_date,
            priority=3
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    # 3. Task list should only show tasks owned or assigned
    def test_tasks_filtered_by_owner_or_assignee(self):
        self.client.login(username="user1", password="pass123")

        project1 = Project.objects.create(name="P1", owner=self.user1)
        project2 = Project.objects.create(name="P2", owner=self.user2)

        Task.objects.create(project=project1, title="Allowed Task", priority=2)
        Task.objects.create(project=project2, title="Blocked Task", priority=2)

        response = self.client.get("/tasks/")
        data = response.json()

        task_titles = [t["title"] for t in data["tasks"]]

        self.assertIn("Allowed Task", task_titles)
        self.assertNotIn("Blocked Task", task_titles)
