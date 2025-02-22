# app/clubs/resources.py
from flask_restful import Resource, reqparse
from flask import g
from functools import wraps
from app.extensions import db
from app.auth.resources import jwt_required
from app.models.user import User
from app.models.club import Club
from app.models.club_membership import ClubMembership
from app.models.book import Book

def get_club(f):
    """ 
    decorator to fetch club object from <unique_id> in the route.
    if club does not exist, return 404
    """ 
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = kwargs.get("unique_id")
        club = Club.query.filter_by(unique_id=uid).first()
        if not club:
            return {"error": "Club not found"}, 404
        g.club = club
        return f(*args, **kwargs)
    return decorated

class ClubsListResource(Resource):
    @jwt_required
    def get(self):
        """
        list all clubs the current user is a member of (and not banned)
        """
        memberships = ClubMembership.query.filter_by(user_id=g.user_id, is_banned=False).all()
        club_ids = [m.club_id for m in memberships]
        clubs = Club.query.filter(Club.id.in_(club_ids)).all()

        return [{
            "unique_id": club.unique_id,
            "creator_id": club.creator_id,
            "name": club.name,
            "created_at": club.created_at.isoformat()
        } for club in clubs], 200

    @jwt_required
    def post(self):
        """
        create a new club. the user becomes the club creator and is automatically joined
        """
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True, help="Club name is required")
        args = parser.parse_args()

        # create the club
        new_club = Club(creator_id=g.user_id, name=args["name"])
        db.session.add(new_club)
        db.session.commit()

        # add membership for creator
        membership = ClubMembership(club_id=new_club.id, user_id=g.user_id, is_banned=False)
        db.session.add(membership)
        db.session.commit()

        return {
            "message": "Club created successfully",
            "unique_id": new_club.unique_id
        }, 201

class ClubResource(Resource):
    @jwt_required
    @get_club
    def get(self, unique_id: str):
        """
        get details about a single club if the user is a member and not banned
        """
        # check membership
        membership = ClubMembership.query.filter_by(
            club_id=g.club.id, 
            user_id=g.user_id
        ).first()

        if not membership or membership.is_banned:
            return {"error": "You are not a member of this club or you are banned"}, 403

        creator = User.query.get(g.club.creator_id)

        return {
            "unique_id": g.club.unique_id,
            "creator_username": creator.username if creator else None,
            "name": g.club.name,
            "created_at": g.club.created_at.isoformat(),
        }, 200

    @jwt_required
    @get_club
    def delete(self, unique_id: str):
        """
        delete the club (creator-only)
        """
        if g.club.creator_id != g.user_id:
            return {"error": "Only the creator can delete this club"}, 403

        # delete memberships first, then club
        ClubMembership.query.filter_by(club_id=g.club.id).delete()
        db.session.delete(g.club)
        db.session.commit()

        return {"message": "Club deleted successfully"}, 200

class ClubJoinResource(Resource):
    @jwt_required
    @get_club
    def post(self, unique_id: str):
        """
        join a user to a club if they are not banned or already in it
        """
        # check for existing membership
        membership = ClubMembership.query.filter_by(
            club_id=g.club.id,
            user_id=g.user_id
        ).first()

        if membership:
            if membership.is_banned:
                return {"error", "You are banned from this club"}, 403
            return {"message", "You are already in this club"}, 200

        # create membership
        membership = ClubMembership(
            club_id=g.club.id,
            user_id=g.user_id,
            is_banned=False
        )
        db.session.add(membership)
        db.session.commit()

        return {"message": "You joined the club successfully"}, 200

class ClubLeaveResource(Resource):
    @jwt_required
    @get_club
    def post(self, unique_id: str):
        """
        user leaves a club they are in
        """
        membership = ClubMembership.query.filter_by(
            club_id=g.club.id,
            user_id=g.user_id
        ).first()

        if not membership or membership.is_banned:
            return {"error": "You are not an active member of this club"}, 403

        if g.club.creator_id == g.user_id:
            return {"error": "Club creators cannot leave their own clubs"}, 403

        db.session.delete(membership)
        db.session.commit()

        return {"message": "You left the club"}, 200

class ClubBanResource(Resource):
    @jwt_required
    @get_club
    def post(self, unique_id: str):
        """
        ban a user from a club (creator-only)
        request json body: { "user_id": <int> }
        """
        if g.club.creator_id != g.user_id:
            return {"error": "Only the club creator can ban users"}, 403

        parser = reqparse.RequestParser()
        parser.add_argument("user_id", type=int, required=True, help="user_id is required")
        args = parser.parse_args()
        target_user_id = args["user_id"]

        # make sure target user exists
        target_user = User.query.get(target_user_id)
        if not target_user: return {"error": "User not found"}, 404

        # get membership row
        membership = ClubMembership.query.filter_by(
            club_id=g.club.id,
            user_id=target_user_id
        ).first()

        # if not membership, create one as banned
        if not membership:
            membership = ClubMembership(club_id=g.club.id, user_id=target_user_id, is_banned=True)
            db.session.add(membership)
        else:
            membership.is_banned = True

        db.session.commit()

        return {"message": f"User {target_user_id} has been banned from club {g.club.unique_id}"}, 200

class ClubMembersResource(Resource):
    @jwt_required
    @get_club
    def get(self, unique_id: str):
        """ 
        list non banned members of this club
        """
        # check membership validity
        membership = ClubMembership.query.filter_by(
            club_id=g.club.id, 
            user_id=g.user_id
        ).first()

        if not membership or membership.is_banned:
            return {"error": "You are not a member of this club or you are banned"}, 403

        # fetch memberships 
        memberships = ClubMembership.query.filter_by(
            club_id=g.club.id, 
            is_banned=False
        ).all()

        # compile user info
        members_data = []
        for m in memberships:
            user = User.query.get(m.user_id)
            if user:
                members_data.append({
                    "id": user.id,
                    "username": user.username,
                })

        return {
            "creator_id": g.club.creator_id,
            "members": members_data
        }, 200

class ClubsCreatedResource(Resource):
    @jwt_required
    def get(self):
        """
        return a list of clubs that the current user created
        """
        clubs = Club.query.filter_by(creator_id=g.user_id).all()

        return [{
            "unique_id": club.unique_id,
            "creator_id": club.creator_id ,
            "name": club.name,
            "created_at": club.created_at.isoformat()
        } for club in clubs], 200

class ClubBooksResource(Resource):
    @jwt_required
    @get_club
    def post(self, unique_id: str):
        """
        add a new book to the club (creator-only)
        """
        if g.club.creator_id != g.user_id:
            return {"error": "Only the creator can add books to this club"}, 403

        parser = reqparse.RequestParser()
        parser.add_argument("title", required=True, help="Title is required")
        parser.add_argument("author", required=True, help="Author is required")
        args = parser.parse_args()

        new_book = Book(
            club_id=g.club.id,
            title=args["title"],
            author=args["author"]
        )
        db.session.add(new_book)
        db.session.commit()

        return {
            "id": new_book.id,
            "title": new_book.title,
            "author": new_book.author,
            "added_at": new_book.added_at.isoformat(),
        }, 201


    @jwt_required
    @get_club
    def get(self, unique_id: str):
        """
        list all books in the club
        """

        membership = ClubMembership.query.filter_by(
            club_id=g.club.id,
            user_id=g.user_id,
            is_banned=False
        ).first()

        if not membership or membership.is_banned:
            return {"error": "You are not an active member of this club"}, 403

        books = Book.query.filter_by(club_id=g.club.id).order_by(Book.added_at.asc()).all()

        return [{
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "added_at": book.added_at.isoformat()
        } for book in books], 200
