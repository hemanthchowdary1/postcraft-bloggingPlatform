# DevBlog 🚀

A full-featured blogging platform built with Django, designed with a modern UI and social interaction features.

---

## ✨ Features
- User Authentication (Login / Signup)
- Email OTP Verification
- Create, Edit, Delete Posts
- Like & 🔖 Bookmark System
- Follow Users
- Notifications System
- Search & Tag Filtering
- Dark / Light Theme UI
- Comments System

---

## 🛠 Tech Stack
- Python
- Django
- SQLite
- HTML, CSS (Custom UI)
- JavaScript (AJAX)

---

## 📸 Screenshots

### 🏠 Home Page
![Home](screenshots/home.png)

### 📄 Post Detail
![Post](screenshots/post.png)
![Post](screenshots/post2.png)

### 👤 Profile Page
![Profile](screenshots/profile.png)

### 🔔 Notifications Page
![Notifications](screenshots/notifications.png)

### ⚙️ Settings Page
![Settings](screenshots/settings.png)

---

## ⚙️ Setup

```bash
git clone https://github.com/hemanthchowdary1/postcraft-bloggingPlatform.git
cd post_craft
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```