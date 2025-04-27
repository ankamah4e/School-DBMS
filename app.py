from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError

app = Flask(__name__, static_folder='./static', static_url_path='/static')
app.secret_key = "your_secret_key"  # Change this to a secure key

# SQL Server connection string
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://ANKAMAH\\SQLEXPRESS/SchoolDB"
    "?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- MODELS ---
class Student(db.Model, UserMixin):  
    __tablename__ = "Students_069"
    StudentID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    DOB = db.Column(db.Date, nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)

    def get_id(self):
        return str(self.StudentID)

class Teacher(db.Model):
    __tablename__ = "Teachers_069"
    TeacherID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Subject = db.Column(db.String(50))

class Course(db.Model):
    __tablename__ = "Courses_069"
    CourseID = db.Column(db.Integer, primary_key=True)
    CourseName = db.Column(db.String(100))
    TeacherID = db.Column(db.Integer, db.ForeignKey("Teachers_069.TeacherID"))

class Enrollment(db.Model):
    __tablename__ = "Enrollments_069"
    EnrollmentID = db.Column(db.Integer, primary_key=True, autoincrement=False)  # No auto-increment
    StudentID = db.Column(db.Integer, db.ForeignKey("Students_069.StudentID"))
    CourseID = db.Column(db.Integer, db.ForeignKey("Courses_069.CourseID"))
    EnrollmentDate = db.Column(db.Date)

class Payment(db.Model):
    __tablename__ = "Payments_069"
    PaymentID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.Integer, db.ForeignKey("Students_069.StudentID"))
    Amount = db.Column(db.Numeric(10, 2))
    PaymentDate = db.Column(db.Date)

class LoginLog(db.Model):
    __tablename__ = "LoginLog"
    LogID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.Integer, db.ForeignKey("Students_069.StudentID"))
    LoginTime = db.Column(db.DateTime, default=db.func.current_timestamp())

class Admin(db.Model):
    __tablename__ = "Admins_069"
    AdminID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Email = db.Column(db.String(100), unique=True)
    Password = db.Column(db.String(100))

    def get_id(self):
        return str(self.AdminID)

# Create tables
with app.app_context():
    db.create_all()

# --- LOGIN MANAGER ---
@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))

# --- ROUTES ---
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/teachers')
def teachers():
    return render_template('teachers.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/')
def home():
    return redirect(url_for('index'))

# Register Student (Using Stored Procedure)
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'admin_id' not in session:  # Only admin can add students
        flash('Please login as admin first', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        email = request.form['email']

        try:
            # Call stored procedure
            query = text("EXEC RegisterStudent :name, :dob, :email")
            db.session.execute(query, {"name": name, "dob": dob, "email": email})
            db.session.commit()
            flash('Student registered successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except IntegrityError as e:
            db.session.rollback()
            flash('Email already exists! Please use a different email.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('add_student.html')

# Student Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form.get('password', '')  # Get password, default to empty string if not provided
        role = request.form['role']

        if role == 'admin':
            admin = Admin.query.filter_by(Email=email).first()
            if admin and admin.Password == password:
                session['admin_id'] = admin.AdminID
                session['admin_name'] = admin.Name
                flash('Welcome back, ' + admin.Name, 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid email or password', 'error')
                return redirect(url_for('login'))
        elif role == 'student':
            student = Student.query.filter_by(Email=email).first()
            if student:
                session['student_id'] = student.StudentID
                session['student_name'] = student.Name
                login_user(student)  # This is needed for @login_required decorator
                # Add login log
                log_entry = LoginLog(StudentID=student.StudentID)
                db.session.add(log_entry)
                db.session.commit()
                flash('Welcome back, ' + student.Name, 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Student not found', 'error')
        elif role == 'teacher':
            try:
                # Try to convert input to integer for teacher ID
                teacher_id = int(email)
                teacher = Teacher.query.filter_by(TeacherID=teacher_id).first()
                if teacher:
                    session['teacher_id'] = teacher.TeacherID
                    session['teacher_name'] = teacher.Name
                    flash('Welcome back, ' + teacher.Name, 'success')
                    return redirect(url_for('teacher_dashboard'))
                else:
                    flash('Teacher ID not found', 'error')
            except ValueError:
                flash('Please enter a valid Teacher ID', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('login.html')

# Student Dashboard (Requires Login)
@app.route('/dashboard')
@login_required
def dashboard():
    # Get courses and teachers for the logged-in student
    courses_with_teachers = db.session.query(
        Course, Teacher
    ).join(
        Enrollment, Course.CourseID == Enrollment.CourseID
    ).join(
        Teacher, Course.TeacherID == Teacher.TeacherID, isouter=True
    ).filter(
        Enrollment.StudentID == current_user.StudentID
    ).all()
    
    return render_template('student_dashboard.html', 
                         courses_with_teachers=courses_with_teachers,
                         current_user=current_user)

# Teacher Dashboard
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('login'))
    
    teacher = Teacher.query.get(session['teacher_id'])
    if not teacher:
        return redirect(url_for('login'))
    
    # Get courses taught by this teacher
    courses = Course.query.filter_by(TeacherID=teacher.TeacherID).all()
    
    # Get students enrolled in each course
    students_by_course = {}
    for course in courses:
        students = Student.query.join(
            Enrollment, Student.StudentID == Enrollment.StudentID
        ).filter(
            Enrollment.CourseID == course.CourseID
        ).all()
        students_by_course[course.CourseID] = students
    
    return render_template('teacher_dashboard.html',
                         teacher=teacher,
                         courses=courses,
                         students_by_course=students_by_course)

# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login as admin first', 'error')
        return redirect(url_for('login'))
    
    admin = Admin.query.get(session['admin_id'])
    if not admin:
        session.pop('admin_id', None)
        session.pop('admin_name', None)
        flash('Admin session invalid', 'error')
        return redirect(url_for('login'))

    students = Student.query.all()
    teachers = Teacher.query.all()
    courses = Course.query.all()

    # Get current enrollments for display
    current_enrollments = db.session.query(
        Student, Course, Teacher
    ).join(
        Enrollment, Student.StudentID == Enrollment.StudentID
    ).join(
        Course, Enrollment.CourseID == Course.CourseID
    ).join(
        Teacher, Course.TeacherID == Teacher.TeacherID
    ).all()

    return render_template('admin_dashboard.html',
                         admin=admin,
                         students=students,
                         teachers=teachers,
                         courses=courses,
                         current_enrollments=current_enrollments)

# Assign Course
@app.route('/assign_course', methods=['POST'])
def assign_course():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    
    if not student_id or not course_id:
        flash('Please select both student and course', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Check if enrollment already exists
    existing_enrollment = Enrollment.query.filter_by(
        StudentID=student_id,
        CourseID=course_id
    ).first()
    
    if existing_enrollment:
        flash('Student is already enrolled in this course', 'warning')
    else:
        try:
            # Get the next available EnrollmentID
            max_id = db.session.query(db.func.max(Enrollment.EnrollmentID)).scalar() or 0
            new_enrollment = Enrollment(
                EnrollmentID=max_id + 1,
                StudentID=student_id,
                CourseID=course_id,
                EnrollmentDate=db.func.current_date()
            )
            db.session.add(new_enrollment)
            db.session.commit()
            flash('Student successfully enrolled in course', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error enrolling student: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Remove Enrollment
@app.route('/remove_enrollment/<int:student_id>/<int:course_id>')
def remove_enrollment(student_id, course_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    enrollment = Enrollment.query.filter_by(
        StudentID=student_id,
        CourseID=course_id
    ).first()
    
    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()
        flash('Enrollment removed successfully', 'success')
    else:
        flash('Enrollment not found', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Assign Teacher
@app.route('/assign_teacher', methods=['POST'])
def assign_teacher():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    teacher_id = request.form.get('teacher_id')
    
    if not course_id or not teacher_id:
        flash('Please select both course and teacher', 'error')
        return redirect(url_for('admin_dashboard'))
    
    course = Course.query.get(course_id)
    if course:
        course.TeacherID = teacher_id
        db.session.commit()
        flash('Teacher successfully assigned to course', 'success')
    else:
        flash('Course not found', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('teacher_id', None)
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return redirect(url_for('login'))

# Admin Route (Restricted)
@app.route('/admin')
@login_required
def admin():
    if current_user.Email != "admin@school.com":  # Replace with actual admin check
        return "Access Denied", 403
    return "Welcome Admin!"

@app.route('/test_db')
def test_db():
    try:
        result = db.session.execute(text("SELECT 1")).scalar()
        return f"Database connection successful: {result}"
    except Exception as e:
        return f"Database connection failed: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)