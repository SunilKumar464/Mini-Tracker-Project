from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db.models import Count, Q
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from .models import Project, Task
import json


# ==================================================
# API LOGIN (JSON ONLY - NO HTML)
# ==================================================
@csrf_exempt
@require_POST
def api_login(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user = authenticate(
        username=data.get("username"),
        password=data.get("password")
    )

    if not user:
        return JsonResponse({"error": "Invalid username or password"}, status=401)

    login(request, user)
    return JsonResponse({"message": "Login successful", "user": user.username})


# ==================================================
# CREATE / LIST PROJECTS
# ==================================================
@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def create_project(request):

    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except:
            return HttpResponseBadRequest("Invalid JSON format")

        name = data.get("name")
        description = data.get("description", "")

        if not name:
            return HttpResponseBadRequest("Project name is required.")

        project = Project(name=name, description=description, owner=request.user)

        try:
            project.full_clean()
            project.save()
        except ValidationError as e:
            return JsonResponse({"errors": e.message_dict}, status=400)

        return JsonResponse({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner": project.owner.username,
        }, status=201)

    # GET
    qs = Project.objects.filter(owner=request.user)
    search = request.GET.get("search")

    if search:
        qs = qs.filter(name__icontains=search)

    return JsonResponse({
        "projects": list(qs.values("id", "name", "description", "created_at", "updated_at"))
    })


# ==================================================
# CREATE TASK
# ==================================================
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_task(request, project_id):

    project = get_object_or_404(Project, id=project_id)

    if project.owner != request.user:
        return HttpResponseForbidden("Only the project owner can create tasks.")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return HttpResponseBadRequest("Invalid JSON format")

    title = data.get("title")
    if not title:
        return HttpResponseBadRequest("Task title is required.")

    try:
        priority = int(data.get("priority"))
    except:
        return JsonResponse({
            "errors": {
                "priority": ["Priority must be between 1 (highest) and 5 (lowest)."]
            }
        }, status=400)

    due_date = parse_date(data.get("due_date")) if data.get("due_date") else None

    assignee = None
    if data.get("assignee_id"):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            assignee = User.objects.get(id=data["assignee_id"])
        except User.DoesNotExist:
            return JsonResponse({"errors": {"assignee_id": ["Assignee not found."]}}, status=400)

    task = Task(
        project=project,
        title=title,
        description=data.get("description", ""),
        priority=priority,
        due_date=due_date,
        assignee=assignee,
        status=data.get("status", Task.STATUS_TODO),
    )

    try:
        task.full_clean()
        task.save()
    except ValidationError as e:
        return JsonResponse({"errors": e.message_dict}, status=400)

    return JsonResponse({
        "id": task.id,
        "title": task.title,
        "project": task.project.id,
    }, status=201)


# ==================================================
# LIST TASKS
# ==================================================
@csrf_exempt
@login_required
def list_tasks(request):

    qs = Task.objects.filter(
        Q(project__owner=request.user) |
        Q(assignee=request.user)
    )

    if request.GET.get("status"):
        qs = qs.filter(status=request.GET["status"])

    if request.GET.get("project_id"):
        qs = qs.filter(project_id=request.GET["project_id"])

    if request.GET.get("due_before"):
        date = parse_date(request.GET["due_before"])
        if not date:
            return HttpResponseBadRequest("Invalid date format. Use YYYY-MM-DD.")
        qs = qs.filter(due_date__lte=date)

    return JsonResponse({
        "tasks": list(qs.values(
            "id", "title", "status",
            "priority", "project_id", "due_date"
        ))
    })


# ==================================================
# DASHBOARD
# ==================================================
# summary-view-anchor
@csrf_exempt
@login_required
def dashboard(request):

    user = request.user

    total_projects = Project.objects.filter(owner=user).count()
    total_tasks = Task.objects.filter(project__owner=user).count()

    status_summary = Task.objects.filter(project__owner=user) \
        .values("status") \
        .annotate(count=Count("status"))

    grouped = {item["status"]: item["count"] for item in status_summary}

    upcoming = Task.objects.filter(
        project__owner=user,
        due_date__isnull=False
    ).exclude(
        status=Task.STATUS_DONE
    ).order_by("due_date")[:5]

    upcoming_tasks = list(upcoming.values("id", "title", "due_date", "priority")) \
        if upcoming.exists() else "No upcoming tasks!"

    return JsonResponse({
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "tasks_by_status": grouped,
        "upcoming_tasks": upcoming_tasks
    })
