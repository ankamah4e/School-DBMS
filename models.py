from app import db

# Student Table
class Student(db.Model):
    __tablename__ = 'Students_069'  # Matches your SQL table name
    StudentID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    DOB = db.Column(db.Date, nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)

# Course Table
class Course(db.Model):
    __tablename__ = 'Courses_069'
    CourseID = db.Column(db.Integer, primary_key=True)
    CourseName = db.Column(db.String(100), nullable=False)

# Enrollment Table (Many-to-Many)
class Enrollment(db.Model):
    __tablename__ = 'Enrollments_069'
    EnrollmentID = db.Column(db.Integer, primary_key=True)
    StudentID = db.Column(db.Integer, db.ForeignKey('Students_069.StudentID'))
    CourseID = db.Column(db.Integer, db.ForeignKey('Courses_069.CourseID'))
