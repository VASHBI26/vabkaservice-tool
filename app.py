from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Dummy database
users_db = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'user1': {'password': 'user123', 'role': 'user'},
    'approver1': {'password': 'approver123', 'role': 'approver'}
}

tickets = []
logs = []
chat_messages = []

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_db.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            logs.append(f"{username} logged in")
            return redirect(url_for(f"{user['role']}_dashboard"))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logs.append(f"{session['username']} logged out")
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', users=users_db, logs=logs)

@app.route('/user/dashboard')
def user_dashboard():
    if session.get('role') != 'user':
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', tickets=tickets)

@app.route('/approver/dashboard')
def approver_dashboard():
    if session.get('role') != 'approver':
        return redirect(url_for('login'))
    return render_template('approver_dashboard.html', tickets=tickets)

@app.route('/create_user', methods=['POST'])
def create_user():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    users_db[username] = {'password': password, 'role': role}
    logs.append(f"Admin created user {username} with role {role}")
    return redirect(url_for('admin_dashboard'))

@app.route('/raise_ticket', methods=['POST'])
def raise_ticket():
    if session.get('role') != 'user':
        return redirect(url_for('login'))
    data = request.form.to_dict()
    file = request.files.get('attachment')
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    data['attachment'] = filename
    data['raised_by'] = session['username']
    tickets.append(data)
    logs.append(f"{session['username']} raised a ticket")
    return redirect(url_for('user_dashboard'))

@app.route('/approve_ticket', methods=['POST'])
def approve_ticket():
    if session.get('role') != 'approver':
        return redirect(url_for('login'))
    ticket_id = int(request.form['ticket_id'])
    decision = request.form['decision']
    tickets[ticket_id]['status'] = decision
    logs.append(f"{session['username']} {decision} ticket ID {ticket_id}")
    return redirect(url_for('approver_dashboard'))

@app.route('/chat', methods=['POST'])
def chat():
    sender = session['username']
    receiver = request.form['receiver']
    message = request.form['message']
    chat_messages.append({'sender': sender, 'receiver': receiver, 'message': message})
    return redirect(url_for(f"{session['role']}_dashboard"))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
