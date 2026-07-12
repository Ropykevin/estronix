"""Category model with hierarchical parent-child support."""

from datetime import datetime, timezone

from slugify import slugify

from app.extensions import db


class Category(db.Model):
    """Product category with optional parent for nesting."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    parent = db.relationship("Category", remote_side=[id], backref=db.backref("children", lazy="dynamic"))
    products = db.relationship("Product", back_populates="category", lazy="dynamic")

    @staticmethod
    def generate_slug(name):
        return slugify(name, max_length=120)

    def get_all_children(self):
        """Return this category and all descendant categories."""
        result = [self]
        for child in self.children.filter_by(is_active=True):
            result.extend(child.get_all_children())
        return result

    def get_breadcrumb(self):
        """Return list of ancestors from root to this category."""
        trail = []
        current = self
        while current:
            trail.insert(0, current)
            current = current.parent
        return trail

    def __repr__(self):
        return f"<Category {self.name}>"
