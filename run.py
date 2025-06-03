# run.py
from myapp import create_app, db

app = create_app()

# Optionally, to create your database tables:
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
