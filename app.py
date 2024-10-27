from flask import Flask, flash, redirect, render_template, request, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.urandom(12)

# Simple in-memory "database" for users
users = {}
tasks = {}

# File to store user and task data
USER_DATA_FILE = 'users.txt'
TASK_DATA_FILE = 'tasks.txt'

def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        username, password = line.split(',')
                        users[username] = {'password': password, 'credits': 10}
                    except ValueError:
                        print(f"Skipping malformed line: {line}")
    
    # Create admin account if it doesn't exist
    if 'admin' not in users:
        users['admin'] = {'password': 'adminpassword', 'credits': 0}
        save_users()

def save_users():
    with open(USER_DATA_FILE, 'w') as f:
        for username, info in users.items():
            f.write(f"{username},{info['password']}\n")

def load_tasks():
    if os.path.exists(TASK_DATA_FILE):
        with open(TASK_DATA_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        username, description, due_date = line.split(',')
                        if username not in tasks:
                            tasks[username] = []
                        tasks[username].append({'description': description, 'due_date': due_date})
                    except ValueError:
                        print(f"Skipping malformed task line: {line}")

def save_task(username, description, due_date):
    with open(TASK_DATA_FILE, 'a') as f:
        f.write(f"{username},{description},{due_date}\n")

def fetch_latest_news():
    url = "https://newsdata.io/api/1/news?country=lb&apikey=pub_570099fb9d079a4c5d292e542f400a91313b7"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        print("Error fetching news:", response.status_code)
        return []

# Load users and tasks when the app starts
load_users()
load_tasks()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        username = session.get('username')
        if username is None:
            return "Error: User not logged in properly."

        # Fetch latest news articles
        latest_news = fetch_latest_news()
        return render_template('logged_in.html', tasks=tasks.get(username, []), username=username, latest_news=latest_news)

@app.route('/login', methods=['POST'])
def do_admin_login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in users and users[username]['password'] == password:
        session['logged_in'] = True
        session['username'] = username
        if username == 'admin':
            return redirect('/admin')
        return redirect('/')
    else:
        flash('Invalid username or password!')
        return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required!')
            return redirect('/signup')

        if username in users:
            flash('Username already exists!')
        else:
            users[username] = {'password': password, 'credits': 10}
            save_users()
            flash('Signup successful! You can now log in.')
            return redirect('/')
    return render_template('signup.html')

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect('/')

@app.route('/add_task', methods=['POST'])
def add_task():
    username = session.get('username')
    task_description = request.form.get('task')
    due_date = request.form.get('due_date')
    
    if username and task_description and due_date:
        if username not in tasks:
            tasks[username] = []
        tasks[username].append({'description': task_description, 'due_date': due_date})
        save_task(username, task_description, due_date)
    return redirect('/')

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    username = session.get('username')
    if username and 0 <= task_id < len(tasks[username]):
        tasks[username].pop(task_id)
        with open(TASK_DATA_FILE, 'w') as f:
            for user, user_tasks in tasks.items():
                for task in user_tasks:
                    f.write(f"{user},{task['description']},{task['due_date']}\n")
    return redirect('/')

@app.route('/admin')
def admin():
    if session.get('logged_in') and session['username'] == 'admin':
        return render_template('admin.html', users=users)
    return redirect('/')

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if session.get('logged_in') and session['username'] == 'admin':
        if username in users and username != 'admin':
            del users[username]
            save_users()
            flash(f'User {username} deleted successfully.')
        else:
            flash('Cannot delete admin or non-existing user.')
        return redirect('/admin')
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)
