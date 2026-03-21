# 🎫 Production-Grade Internal Ticketing System

A lightweight, secure, and multi-user internal ticketing system built with **Streamlit** and **SQLite**. Designed for small teams (5–10 users) to track UAT and deployment issues with full audit accountability.

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have Python 3.8+ installed.

### 2. Setup
Clone the repository and install dependencies:
```bash
git clone https://github.com/sraj-sudo/project_management.git
cd project_management
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```

### 4. Default Login
- **Username**: `admin`
- **Password**: `admin123`

---

## 🛠️ Key Functionality

### 🔐 Advanced Security
- **Bcrypt Hashing**: Passwords are never stored in plain text.
- **Backend Role Enforcement**: Every sensitive database operation (updates, assignments, user creation) verifies the user's role against the database, ensuring integrity even if the UI is bypassed.
- **Page-Level Guards**: Direct URL access to restricted pages (e.g., Analytics for Reporters) is automatically blocked.

### 👥 Role-Based Workflows
- **Admin**: Full system control, user management, task assignment, and high-level analytics.
- **Developer**: Specialized dashboard and Kanban view showing only assigned tasks. Managed workflow transitions (New ➡️ In Progress ➡️ Testing ➡️ Closed).
- **Reporter**: Simple form to submit bugs, enhancements, or feedback.

### 📊 Powerful Tracking & Analytics
- **Audit History**: Every status change is recorded with timestamps and the identity of the modifier.
- **Live Kanban**: Visual column-based progress tracking.
- **Interactive Analytics**: Data distribution charts (Status, Priority, Type) using Plotly.
- **CSV Export**: Export filtered data for external reporting or archival.

---

## 📂 Project Structure

- `app.py`: Main entry point, login logic, and dynamic sidebar.
- `pages/`: Multi-page functional modules (Reporting, Dashboard, Kanban, Analytics, User Management).
- `utils/`: Core logic (Authentication, Database, Helpers, Drive).
- `data/`: SQLite database storage (`issues.db`).
- `uploads/`: Local storage for issue attachments.

---

## 🧪 Testing & Verification

The project includes an automated backend verification suite `verify_system.py`.

### Run Backend Tests:
```bash
python3 verify_system.py
```
**Tests Covered**:
- [x] Bcrypt Password Hashing & Verification
- [x] Safe Database Seeding (No duplicates)
- [x] Role-Based Access Restriction (Authorized vs Unauthorized status updates)
- [x] Transition Logic Enforcement (Workflow deadlocks and invalid shifts)

---

## 👤 Admin User Management
Admins can create new users via the **User Management** page:
1. Navigate to "User Management" in the sidebar.
2. Enter username, password, and select a role (`admin`, `developer`, `reporter`).
3. View the list of all active users in the system.

---

## 📝 License
This project is open-source and intended for internal team use.
