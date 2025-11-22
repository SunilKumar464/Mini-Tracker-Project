A Django-based application to manage projects and tasks for multiple users with secure session authentication and ORM-based dashboard reporting.


🚀 Tech Stack

Python 3.11+

Django 5.x (LTS)

SQLite (default)

Django ORM

Session Authentication



📦 Installation & Setup
1. Create project
Mkdir minitracker
cd minitracker

2. Create Virtual Environment
python -m venv minivenv  
minivenv\Scripts\activate          # Windows

3. Install Dependencies
pip install django

▶ Run Migrations & Start Server
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py test tracker



Open:

http://127.0.0.1:8000/

👤 Create Test User (Optional)
python manage.py createsuperuser


Then login:

http://127.0.0.1:8000/accounts/login/


The Admin:

http://127.0.0.1:8000/admin/

✅ Implemented Features

Project management with unique project names per user.

Task creation with strict validation.

Ownership & assignee based filtering.

Session-based authentication.

Efficient dashboard statistics using ORM aggregation.

🔐 Authentication & Access Protection

All endpoints require authenticated users.

Login handled via Django session system.

Only project owners can create tasks in that project.



📊 Dashboard Implementation

Uses Django ORM aggregation and annotations for performance.

Includes:

Total projects

Total tasks

Tasks grouped by status

Top 5 upcoming tasks

NOTE: I have implemented the dashboard using ORM aggregation, not manual Python loops.



🧠 Data Modeling Summary

Project → Unique per owner (name + owner constraint)

Task → Linked to Project and optional Assignee

Validation inside model clean() method ensures:

Priority range 1–5

No future due_date if status = done



✅ Required API Endpoints
Method	URL	Purpose
POST	/projects/	Create project
GET	/projects/	List projects + search
POST	/projects/<id>/tasks/	Create task
GET	/tasks/	Filtered task list
GET	/dashboard/	User dashboard summary