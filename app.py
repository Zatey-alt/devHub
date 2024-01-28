from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests

from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = '2s45d5d5d4s5sd45d4dklhgsd5s5d4d5s58fd4f'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/profile_pics' 

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'signin'

# Function to save profile image
def save_profile_image(file):
    # Check if the file is allowed
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        # Securely save the file
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    else:
        return None

# Function to generate a secure filename
def generate_secure_filename(filename):
    return secure_filename(filename)

# User model for database
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')

    def save_user_image(self, image):
        # Use the generate_secure_filename function to create a secure filename
        filename = generate_secure_filename(image.filename)
        # Save the image to a specific folder (e.g., 'static/profile_pics/')
        image.save(os.path.join(app.root_path, 'static', 'profile_pics', filename))
        # Update the user's image_file field with the filename
        self.image_file = filename

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id', ondelete='CASCADE'), nullable=False)
    def __repr__(self):
        return f"Comment('{self.content}', '{self.author}', '{self.created_at}')"


# Modify the Blog model to include the relationship with Comment
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(50))
    image_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_image = db.Column(db.String(255))

    # Add a relationship to comments
    comments = db.relationship('Comment', backref='blog', lazy=True)

    def __repr__(self):
        return f"Blog('{self.title}', '{self.author}', '{self.created_at}')"


    def save_blog_image(self, image):
        # Use the generate_secure_filename function to create a secure filename
        filename = generate_secure_filename(image.filename)
        # Save the image to a specific folder (e.g., 'static/blog_images/')
        image.save(os.path.join(app.root_path, 'static', 'blog_images', filename))
        # Update the blog's image_file field with the filename
        self.image_file = filename

# Flask-Login configuration
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Routes
@app.route('/')
def home():
    blogs = Blog.query.all()
    users = User.query.all()
    comments = []

    # Fetch comments separately for each blog
    for blog in blogs:
        blog_comments = Comment.query.filter_by(blog_id=blog.id).all()
        comments.extend(blog_comments)

    return render_template('index.html', blogs=blogs, users=users, comments=comments, user=current_user)




@app.route('/homepage')
@login_required
def homepage():
    # Check if the user is logged in
    if current_user.is_authenticated:
        # Fetch blogs created by the current user
        user_blogs = Blog.query.filter_by(author=current_user.username).all()
        return render_template('homepage.html', blogs=user_blogs)
    else:
        # Fetch all blogs if the user is not logged in
        blogs = Blog.query.all()
    return render_template('homepage.html', blogs=blogs)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Email already exists. Please choose a different email.', 'danger')
            return render_template('signup.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created! You can now sign in.', 'success')
        return redirect(url_for('signin'))

    return render_template('signup.html')



@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        # If the user is already logged in, redirect them to the homepage
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Login failed. Check your email and password.', 'danger')

    return render_template('signin.html')


@app.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('home'))




@app.route('/add_blog', methods=['GET', 'POST'])
@login_required
def add_blog():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = current_user.username
        topic = request.form.get('topic')

        # Fetch the current user's profile image
        author_image = current_user.image_file

        # Check if an image is uploaded for the blog post
        if 'blog_image' in request.files:
            blog_image = request.files['blog_image']
            if blog_image.filename != '':
                # Save the blog image
                new_blog_image = save_blog_image(blog_image)
                if not new_blog_image:
                    flash('Invalid file format for blog image. Please use PNG, JPG, JPEG, or GIF.', 'danger')
                    return redirect(url_for('homepage'))
            else:
                new_blog_image = None
        else:
            new_blog_image = None

        new_blog = Blog(
            title=title,
            content=content,
            author=author,
            image_file=new_blog_image,
            topic=topic,
            author_image=author_image,  
            created_at=datetime.utcnow()
        )

        db.session.add(new_blog)
        db.session.commit()

        flash('Blog post added successfully!', 'success')
        return redirect(url_for('homepage'))




# Helper function to save blog images
def save_blog_image(file):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        filename = generate_secure_filename(file.filename)
        file.save(os.path.join(app.root_path, 'static', 'blog_images', filename))
        return filename
    else:
        return None

  
# Helper function to save profile image
def save_profile_image(file):
    if file is not None and '.' in file.filename:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            # Securely save the file
            filename = generate_secure_filename(file.filename)
            file.save(os.path.join(app.root_path, 'static', 'profile_pics', filename))
            return filename
    return None

@app.route('/delete_blog/<int:blog_id>')
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get(blog_id)

    if blog:
        # Delete associated comments first
        Comment.query.filter_by(blog_id=blog.id).delete()
        db.session.commit()

        # Then delete the blog post
        db.session.delete(blog)
        db.session.commit()

        flash('Blog post and associated comments deleted successfully!', 'success')

    return redirect(url_for('homepage'))


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Check if the current user is trying to update their own profile
    if current_user.id != int(request.form['user_id']):
        flash('You are not allowed to update another user\'s profile', 'danger')
        return redirect(url_for('profile'))

    # Get the file from the request
    file = request.files['profile_image']

    # Save the file to your static folder or another location
    # Generate a unique filename to avoid conflicts
    filename = save_profile_image(file)

    # Update the user's profile_image field in the database
    if filename:
        current_user.image_file = filename

    # Update other profile information
    current_user.username = request.form['username']

    # Commit changes to the database
    db.session.commit()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))


@app.route('/blog/<int:blog_id>', methods=['GET', 'POST'])
def blog(blog_id):
    users = User.query.all()
    blog = Blog.query.get_or_404(blog_id)
    comments = Comment.query.filter_by(blog_id=blog.id).all()

    if request.method == 'POST':
        # Process the comment form submission
        content = request.form['comment_content']
        author = current_user.username

        new_comment = Comment(content=content, author=author, blog_id=blog.id)
        db.session.add(new_comment)
        db.session.commit()

        flash('Comment added successfully!', 'success')
        return redirect(url_for('blog', blog_id=blog.id))

    return render_template('blog.html', blog=blog, comments=comments, users=users)




@app.route('/edit_blog/<int:blog_id>', methods=['GET'])
@login_required
def edit_blog(blog_id):
    # Fetch the blog to be edited
    blog = Blog.query.get(blog_id)

    if not blog:
        flash('Blog not found', 'danger')
        return redirect(url_for('homepage'))

    if current_user.username != blog.author:
        flash('You are not allowed to edit this blog', 'danger')
        return redirect(url_for('homepage'))

    return render_template('edit_blog.html', blog=blog)

@app.route('/edit_blog/<int:blog_id>', methods=['POST'])
@login_required
def update_blog(blog_id):
    # Fetch the blog to be updated
    blog = Blog.query.get(blog_id)

    if not blog:
        flash('Blog not found', 'danger')
        return redirect(url_for('homepage'))

    if current_user.username != blog.author:
        flash('You are not allowed to edit this blog', 'danger')
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        # Update blog details based on the submitted form
        blog.title = request.form['title']
        blog.content = request.form['content']
        blog.topic = request.form.get('topic')

        # Save the updated blog details to the database
        db.session.commit()

        flash('Blog edited successfully!', 'success')

    return redirect(url_for('homepage'))




@app.route('/jobs')
def jobs():
    # ArbeitNow API endpoint for job listings
    api_url = 'https://arbeitnow.com/api/job-board-api'

    # You can customize the parameters based on your needs
    params = {
        'page': 1,  # Specify the page number (you can paginate through results)
        # Add more parameters if needed
    }

    # Make the API request
    response = requests.get(api_url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        jobs_data = response.json()

        # Render the template with the job data
        return render_template('jobs.html', jobs=jobs_data['data'])
    else:
        # If the request was unsuccessful, handle the error
        return f"Error: {response.status_code}"


@app.route('/add_comment/<int:blog_id>', methods=['POST'])
@login_required
def add_comment(blog_id):
    if request.method == 'POST':
        content = request.form['comment_content']
        author = current_user.username

        # Make sure to provide the blog_id when creating a new comment
        new_comment = Comment(content=content, author=author, blog_id=blog_id)
        db.session.add(new_comment)
        db.session.commit()

        flash('Comment added successfully!', 'success')
        return redirect(url_for('blog', blog_id=blog_id))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
