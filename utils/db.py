import sqlite3
import os
import bcrypt
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'issues.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Issues table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id TEXT UNIQUE,
        title TEXT NOT NULL,
        description TEXT,
        type TEXT NOT NULL,
        priority TEXT NOT NULL,
        module TEXT,
        status TEXT DEFAULT 'New',
        assigned_to TEXT,
        tags TEXT,
        file_path TEXT,
        drive_link TEXT,
        reporter TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Comments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id TEXT NOT NULL,
        user TEXT NOT NULL,
        text TEXT NOT NULL,
        type TEXT DEFAULT 'public',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (issue_id)
    )
    ''')
    
    # Issue history table (Audit Trail)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issue_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT,
        changed_by TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (issue_id)
    )
    ''')
    
    # Safe Admin Seeding
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_hashed = hash_password("admin123")
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ('admin', admin_hashed, 'admin'))
    
    conn.commit()
    conn.close()

# User Management
def create_user(username, password, role, creator_role):
    if creator_role != 'admin':
        raise Exception("Unauthorized: Only admins can create users.")
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hashed = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       (username, hashed, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def list_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role, created_at FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

# Issue Logic
def add_issue(issue_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO issues (title, description, type, priority, module, reporter, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        issue_data['title'],
        issue_data['description'],
        issue_data['type'],
        issue_data['priority'],
        issue_data.get('module'),
        issue_data['reporter'],
        'New'
    ))
    
    row_id = cursor.lastrowid
    type_prefix = issue_data['type'][:3].upper() if issue_data['type'] != 'Enhancement' else 'ENH'
    issue_id = f"{type_prefix}-{row_id:03d}"
    
    cursor.execute('''
    UPDATE issues 
    SET issue_id = ?, file_path = ?, drive_link = ?
    WHERE id = ?
    ''', (issue_id, issue_data.get('file_path'), issue_data.get('drive_link'), row_id))
    
    cursor.execute('''
    INSERT INTO issue_history (issue_id, old_status, new_status, changed_by)
    VALUES (?, ?, ?, ?)
    ''', (issue_id, None, 'New', issue_data['reporter']))
    
    conn.commit()
    conn.close()
    return issue_id

def update_issue_status(issue_id, new_status, changed_by, current_user_role):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get current status and assignment
    cursor.execute('SELECT status, assigned_to FROM issues WHERE issue_id = ?', (issue_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
        
    old_status = row['status']
    assigned_to = row['assigned_to']
    
    # Role Enforcement
    if current_user_role == 'reporter':
        conn.close()
        raise Exception("Unauthorized: Reporters cannot change issue status.")
    
    if current_user_role == 'developer':
        if assigned_to != changed_by:
            conn.close()
            raise Exception("Unauthorized: Developers can only update assigned issues.")
        
        # Transition checks
        allowed_transitions = {
            'New': ['In Progress'],
            'In Progress': ['Testing'],
            'Testing': ['Closed', 'In Progress']
        }
        if new_status not in allowed_transitions.get(old_status, []):
            conn.close()
            raise Exception(f"Unauthorized: Developer cannot transition from {old_status} to {new_status}.")

    # Update status
    cursor.execute('UPDATE issues SET status = ? WHERE issue_id = ?', (new_status, issue_id))
    
    # Record history
    cursor.execute('''
    INSERT INTO issue_history (issue_id, old_status, new_status, changed_by)
    VALUES (?, ?, ?, ?)
    ''', (issue_id, old_status, new_status, changed_by))
    
    conn.commit()
    conn.close()
    return True

def assign_issue(issue_id, username, current_user_role):
    if current_user_role != 'admin':
        raise Exception("Unauthorized: Only admins can assign issues.")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE issues SET assigned_to = ? WHERE issue_id = ?", (username, issue_id))
    conn.commit()
    conn.close()

def add_comment(issue_id, user, text, comment_type='public'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO comments (issue_id, user, text, type)
    VALUES (?, ?, ?, ?)
    ''', (issue_id, user, text, comment_type))
    conn.commit()
    conn.close()

def get_issues(filters=None, current_user=None, current_user_role=None):
    conn = get_connection()
    query = "SELECT * FROM issues WHERE 1=1"
    params = []
    
    # Developer Level Filtering (Implicit in UI but enforced here)
    if current_user_role == 'developer' and current_user:
        query += " AND assigned_to = ?"
        params.append(current_user)
    
    if filters:
        if filters.get('type'):
            query += " AND type = ?"
            params.append(filters['type'])
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('priority'):
            query += " AND priority = ?"
            params.append(filters['priority'])
        if filters.get('assigned_to'):
            query += " AND assigned_to = ?"
            params.append(filters['assigned_to'])
        if filters.get('search'):
            query += " AND (title LIKE ? OR issue_id LIKE ?)"
            search_param = f"%{filters['search']}%"
            params.extend([search_param, search_param])
            
    query += " ORDER BY created_at DESC"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    issues = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return issues

def get_issue_details(issue_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM issues WHERE issue_id = ?", (issue_id,))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        return None
        
    issue = dict(issue)
    
    cursor.execute("SELECT * FROM comments WHERE issue_id = ? ORDER BY timestamp ASC", (issue_id,))
    issue['comments'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM issue_history WHERE issue_id = ? ORDER BY timestamp ASC", (issue_id,))
    issue['history'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return issue

if __name__ == '__main__':
    init_db()
    print("Database and users table initialized with safe admin seeding.")
