# myapp/models.py

from .extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)  # hashed pw

    # backref so you can do: current_user.attempts
    attempts = db.relationship(
        'QuizAttempt',
        backref='user',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class QuizAttempt(db.Model):
    __tablename__  = 'quiz_attempt'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(
                        db.Integer,
                        db.ForeignKey('user.id'),
                        nullable=False,
                        index=True
                    )
    taken_on       = db.Column(
                        db.DateTime,
                        default=datetime.utcnow,
                        nullable=False,
                        index=True
                    )
    correct_count  = db.Column(db.Integer, nullable=False)
    total_count    = db.Column(db.Integer, nullable=False)

    @property
    def accuracy(self):
        if self.total_count:
            return round(100 * self.correct_count / self.total_count, 1)
        return 0

    def __repr__(self):
        return (
          f"QuizAttempt(user_id={self.user_id}, "
          f"accuracy={self.accuracy}%, taken_on={self.taken_on})"
        )
