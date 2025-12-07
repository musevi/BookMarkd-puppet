from extensions import db

class Club(db.Model):
    __tablename__ = "club"

    club_id = db.Column(db.Integer, primary_key=True)
    club_name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.Text)

    user_clubs = db.relationship("UserClub", back_populates="club", cascade="all, delete-orphan")
    posts = db.relationship("ClubPost", back_populates="club", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Club {self.club_name}>"
