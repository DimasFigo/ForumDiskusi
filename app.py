from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy 
from markupsafe import Markup
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci-rahasia-yang-sangat-tidak-aman'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    avatar_url = db.Column(db.String(120), nullable=False, default='default-avatar.jpeg')
    
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus login untuk mengakses halaman ini.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
        user = db.session.execute(db.text(query)).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# --- FITUR ADMIN ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if session['role'] != 'admin': return "Akses Ditolak!", 403
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if session['role'] != 'admin': return "Akses Ditolak!", 403
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash(f'Username "{username}" sudah ada!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash(f'Pengguna "{username}" berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if session['role'] != 'admin':
        return "Akses Ditolak!", 403
    if user_id == session.get('user_id'):
        flash('Anda tidak dapat menghapus akun Anda sendiri!', 'danger')
        return redirect(url_for('admin_dashboard'))
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Pengguna "{user_to_delete.username}" dan semua datanya berhasil dihapus.', 'success')
    else:
        flash('Pengguna tidak ditemukan.', 'warning')
    return redirect(url_for('admin_dashboard'))
    
@app.route('/admin/edit_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_password(user_id):
    if session['role'] != 'admin': return "Akses Ditolak!", 403
    user_to_edit = db.session.get(User, user_id)
    if not user_to_edit: return "User tidak ditemukan", 404
    if request.method == 'POST':
        new_password = request.form['new_password']
        user_to_edit.password = new_password 
        db.session.commit()
        flash(f'Password untuk "{user_to_edit.username}" berhasil diganti!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_password.html', user=user_to_edit)

@app.route('/admin/posts')
@login_required
def admin_manage_posts():
    if session['role'] != 'admin': return "Akses Ditolak!", 403
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('admin_posts.html', posts=posts, active_page='posts')

@app.route('/admin/delete_post/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    if session['role'] != 'admin':
        return "Akses Ditolak!", 403

    post_to_delete = db.session.get(Post, post_id)
    if post_to_delete:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash(f'Postingan "{post_to_delete.title}" berhasil dihapus.', 'success')
    else:
        flash('Postingan tidak ditemukan.', 'warning')
    
    return redirect(url_for('admin_manage_posts'))

@app.route('/admin/comments')
@login_required
def admin_manage_comments():
    if session['role'] != 'admin': return "Akses Ditolak!", 403
    comments = Comment.query.order_by(Comment.date_posted.desc()).all()
    return render_template('admin_comments.html', comments=comments, active_page='comments')

@app.route('/admin/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def admin_delete_comment(comment_id):
    if session['role'] != 'admin':
        return "Akses Ditolak!", 403

    comment_to_delete = db.session.get(Comment, comment_id)
    if comment_to_delete:
        db.session.delete(comment_to_delete)
        db.session.commit()
        flash(f'Komentar berhasil dihapus.', 'success')
    else:
        flash('Komentar tidak ditemukan.', 'warning')
    
    return redirect(url_for('admin_manage_comments'))

# --- FITUR USER ---
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('user_dashboard.html', posts=posts)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_detail(post_id):
    post = db.session.get(Post, post_id)
    if not post: return "Postingan tidak ditemukan", 404
    
    if request.method == 'POST':
        comment_content = request.form.get('comment_content')
        if comment_content:
            new_comment = Comment(content=comment_content, user_id=session['user_id'], post_id=post.id)
            db.session.add(new_comment)
            db.session.commit()
            flash('Komentar Anda telah ditambahkan!', 'success')
            return redirect(url_for('post_detail', post_id=post.id))

    post.content = Markup(post.content)
    for comment in post.comments:
        comment.content = Markup(comment.content)
            
    return render_template('post_detail.html', post=post)
    
@app.route('/user/add_post', methods=['POST'])
@login_required
def add_post():
    title = request.form['title']
    content = request.form['content']
    new_post = Post(title=title, content=content, user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    flash('Postingan berhasil ditambahkan!', 'success')
    return redirect(url_for('user_dashboard'))
    
@app.route('/user/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post_to_delete = db.session.get(Post, post_id)
    if post_to_delete:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash('Postingan berhasil dihapus.', 'success')
    else:
        flash('Postingan tidak ditemukan.', 'danger')
    return redirect(url_for('user_dashboard'))
    
@app.route('/user/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post_to_edit = db.session.get(Post, post_id)
    if not post_to_edit: return "Postingan tidak ditemukan", 404

    if post_to_edit.author.id != session['user_id']:
        flash('Anda tidak memiliki izin untuk mengedit postingan ini!', 'danger')
        return redirect(url_for('user_dashboard'))
        
    if request.method == 'POST':
        post_to_edit.title = request.form['title']
        post_to_edit.content = request.form['content']
        db.session.commit()
        flash('Postingan berhasil diperbarui!', 'success')
        return redirect(url_for('user_dashboard'))
    return render_template('edit_post.html', post=post_to_edit)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)