from extensions import db
from datetime import datetime

class ClubComment(db.Model):
    __tablename__ = "club_comment"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("club_post.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    post = db.relationship("ClubPost", back_populates="comments")
    author = db.relationship("User", backref="club_comments", foreign_keys=[author_id])

    @property
    def author_username(self):
        return self.author.username if self.author else None

    def __repr__(self):
        return f"<ClubComment {self.id}>"