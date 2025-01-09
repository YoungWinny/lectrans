from app import create_app
from app.models import Class, Course
from app.database import db

app = create_app()

def create_sample_data():
    """Create sample data for development"""
    with app.app_context():
        # Only create sample data if no classes exist
        if Class.query.first() is None:
            # Create classes
            first_year = Class(name='First Year', academic_year='2023-2024')
            second_year = Class(name='Second Year', academic_year='2023-2024')
            db.session.add_all([first_year, second_year])
            db.session.commit()

            # Create courses
            courses = [
                Course(name='Introduction to Programming', instructor='Dr. Nguh', class_id=first_year.id),
                Course(name='Data Structures', instructor='Dr. Messio', class_id=first_year.id),
                Course(name='Algorithms', instructor='Dr. Ndenge', class_id=second_year.id),
                Course(name='Database Systems', instructor='Dr. Asane', class_id=second_year.id)
            ]
            db.session.add_all(courses)
            db.session.commit()

if __name__ == '__main__':
    create_sample_data()  # Create sample data for development
    app.run(debug=True)