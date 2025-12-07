from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Club, UserClub, ClubPost, ClubComment
from extensions import db
import re
from sqlalchemy.orm import selectinload

clubs_bp = Blueprint('clubs', __name__)

@clubs_bp.route('/clubs', methods=['GET'])
def get_clubs():
    """
    Return all clubs in the database (public endpoint).
    """
    clubs = Club.query.all()
    result = []
    for c in clubs:
        result.append({
            "id": c.club_id,
            "name": c.club_name,
            "slug": c.slug,
            "description": c.description,
        })
    return jsonify(result), 200


@clubs_bp.route('/clubs/mine', methods=['GET'])
@jwt_required()
def get_my_clubs():
    """
    Return all clubs the authenticated user is a member of.
    """
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token subject'}), 422

    memberships = UserClub.query.filter_by(user_id=user_id).all()
    club_ids = [m.club_id for m in memberships]
    if not club_ids:
        return jsonify([]), 200
    clubs = Club.query.filter(Club.club_id.in_(club_ids)).all()
    result = []
    for c in clubs:
        result.append({
            "id": c.club_id,
            "name": c.club_name,
            "slug": c.slug,
            "description": c.description,
        })
    return jsonify(result), 200

@clubs_bp.route('/clubs', methods=['POST'])
@jwt_required()
def create_club():
    """
    Create a new club. The creating user becomes a member.

    Expected JSON body: { "name": "Club Name", "description": "optional" }
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    name = (data.get('name') or data.get('club_name') or '').strip()
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Club name is required'}), 400

    # generate a slug from name
    def _slugify(s: str) -> str:
        s = s.strip().lower()
        # replace non-alphanumeric with hyphens
        s = re.sub(r'[^a-z0-9]+', '-', s)
        s = s.strip('-')
        return s or 'club'

    base_slug = _slugify(name)
    slug = base_slug
    # ensure uniqueness by appending suffix if needed
    counter = 1
    while Club.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    try:
        club = Club(club_name=name, slug=slug, description=description)
        db.session.add(club)
        db.session.flush()  # get club_id

        # add membership for creator
        membership = UserClub(user_id=int(user_id), club_id=club.club_id)
        db.session.add(membership)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create club'}), 500

    return jsonify({
        'id': club.club_id,
        'name': club.club_name,
        'slug': club.slug,
        'description': club.description
    }), 201


@clubs_bp.route('/clubs/<slug>', methods=['GET'])
def get_club(slug):
    """
    Get details for a club by slug.
    """
    club = Club.query.filter_by(slug=slug).first()
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    return jsonify({
        'id': club.club_id,
        'name': club.club_name,
        'slug': club.slug,
        'description': club.description
    }), 200


@clubs_bp.route('/clubs/<slug>/join', methods=['POST'])
@jwt_required()
def join_club(slug):
    """
    Authenticated user joins the club with the given slug.
    """
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token subject'}), 422

    club = Club.query.filter_by(slug=slug).first()
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    # Check if already a member
    existing = UserClub.query.filter_by(user_id=user_id, club_id=club.club_id).first()
    if existing:
        return jsonify({'message': 'Already a member'}), 200

    try:
        membership = UserClub(user_id=user_id, club_id=club.club_id)
        db.session.add(membership)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to join club'}), 500

    return jsonify({'message': 'Joined club', 'club': {
        'id': club.club_id,
        'name': club.club_name,
        'slug': club.slug,
        'description': club.description
    }}), 200

@clubs_bp.route('/clubs/<slug>/posts', methods=['POST'])
@jwt_required()
def create_post(slug):
    """
    Create a post in a club. User must be a member.
    """
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token subject'}), 422

    club = Club.query.filter_by(slug=slug).first()
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    # Check membership
    membership = UserClub.query.filter_by(user_id=user_id, club_id=club.club_id).first()
    if not membership:
        return jsonify({'error': 'Not a member of this club'}), 403

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'error': 'Post body is required'}), 400

    try:
        post = ClubPost(club_id=club.club_id, author_id=user_id, body=body)
        db.session.add(post)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to create post'}), 500

    return jsonify({
        'id': post.id,
        'club_id': post.club_id,
        'author_id': post.author_id,
        'author': post.author_username,
        'body': post.body,
        'created_at': post.created_at.isoformat()
    }), 201

@clubs_bp.route('/clubs/<slug>/feed', methods=['GET'])
@jwt_required()
def club_feed(slug):
    """
    Get paginated posts (with comments) for a club. User must be a member.
    Query params: page (default 1), per_page (default 10, max 50)
    """
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token subject'}), 422

    club = Club.query.filter_by(slug=slug).first()
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    if not UserClub.query.filter_by(user_id=user_id, club_id=club.club_id).first():
        return jsonify({'error': 'Not a member of this club'}), 403

    # Pagination params
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        return jsonify({'error': 'Invalid pagination params'}), 400
    per_page = max(1, min(per_page, 50))
    page = max(1, page)

    # Query posts with selectinload for comments
    post_query = ClubPost.query.options(selectinload(ClubPost.comments)).filter_by(club_id=club.club_id).order_by(ClubPost.created_at.desc())
    pagination = post_query.paginate(page=page, per_page=per_page, error_out=False)
    posts = pagination.items

    feed = []
    for post in posts:
        feed.append({
            'id': post.id,
            'author_id': post.author_id,
            'author': post.author_username,
            'body': post.body,
            'created_at': post.created_at.isoformat(),
            'comments': [
                {
                    'id': c.id,
                    'author_id': c.author_id,
                    'author': c.author_username,
                    'body': c.body,
                    'created_at': c.created_at.isoformat()
                } for c in sorted(post.comments, key=lambda c: c.created_at)
            ]
        })

    return jsonify({
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages,
        'feed': feed
    }), 200


@clubs_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """
    Add a comment to a post. User must be a member of the club.
    """
    user_id = get_jwt_identity()
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token subject'}), 422

    post = ClubPost.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Check membership
    club_id = post.club_id
    membership = UserClub.query.filter_by(user_id=user_id, club_id=club_id).first()
    if not membership:
        return jsonify({'error': 'Not a member of this club'}), 403

    data = request.get_json(silent=True) or {}
    body = (data.get('body') or '').strip()
    if not body:
        return jsonify({'error': 'Comment body is required'}), 400

    try:
        comment = ClubComment(post_id=post_id, author_id=user_id, body=body)
        db.session.add(comment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to add comment'}), 500

    return jsonify({
        'id': comment.id,
        'post_id': comment.post_id,
        'author_id': comment.author_id,
        'author': comment.author_username,
        'body': comment.body,
        'created_at': comment.created_at.isoformat()
    }), 201