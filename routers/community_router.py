import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import User, CommunityPost, PostLike, PostBookmark
from auth import get_current_user, get_optional_user
from services.image_service import save_image, get_image_url

router = APIRouter(prefix="/community", tags=["community"])

CATEGORIES = {"Disease Control", "Yield Tip", "Question", "Market Tip", "Success Story", "Farming Tip"}
MAX_LIMIT = 50
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_POST_TAGS = 10
IST_OFFSET = timedelta(hours=5, minutes=30)


@router.get("/posts")
def get_posts(
    skip: int = 0,
    limit: int = 20,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    saved: bool = False,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    limit = max(1, min(limit, MAX_LIMIT))
    q = db.query(CommunityPost)
    if tag and tag != "All":
        q = q.filter(CommunityPost.tag == tag)
    if search:
        q = q.filter(
            CommunityPost.title.ilike(f"%{search}%") |
            CommunityPost.body.ilike(f"%{search}%")
        )
    if saved:
        if not current_user:
            raise HTTPException(status_code=401, detail="Log in to see saved posts")
        q = q.join(PostBookmark, PostBookmark.post_id == CommunityPost.id)\
            .filter(PostBookmark.user_id == current_user.id)
    posts = q.order_by(CommunityPost.created_at.desc(), CommunityPost.id.desc())\
        .offset(skip).limit(limit).all()
    return _posts_out(db, posts, current_user)


@router.post("/posts")
async def create_post(
    title: str = Form(...),
    body: str = Form(...),
    tag: str = Form(...),
    emoji: str = Form("🌿"),
    post_tags: str = Form("[]"),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    title, body = title.strip(), body.strip()
    if not 5 <= len(title) <= 255:
        raise HTTPException(status_code=400, detail="Title must be 5–255 characters")
    if len(body) < 20:
        raise HTTPException(status_code=400, detail="Body too short")
    if tag not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Unknown post category")

    try:
        tags = json.loads(post_tags)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="post_tags must be a JSON list")
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise HTTPException(status_code=400, detail="post_tags must be a list of strings")
    unique = {}   # case-insensitive: "Wheat" and "wheat" are one tag
    for t in tags:
        t = t.strip()[:40]
        if t:
            unique.setdefault(t.lower(), t)
    tags = list(unique.values())[:MAX_POST_TAGS]

    image_path = None
    if image and image.filename:
        image_bytes = await image.read()
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        try:
            image_path = save_image(image_bytes, prefix="post")
        except Exception:
            raise HTTPException(status_code=400, detail="File is not a valid image")

    post = CommunityPost(
        user_id=current_user.id,
        title=title,
        body=body,
        tag=tag,
        emoji=(emoji or "🌿")[:10],
        post_tags=tags,
        image_path=image_path,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(post, user_id=current_user.id)


@router.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle the current user's like."""
    post = _get_post(db, post_id)
    liked = _toggle(db, PostLike, current_user.id, post_id)
    # Count from the likes table so the number always matches who liked it.
    post.likes = db.query(func.count(PostLike.id)).filter(PostLike.post_id == post_id).scalar()
    db.commit()
    return {"liked": liked, "likes": post.likes}


@router.post("/posts/{post_id}/bookmark")
def bookmark_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle the current user's bookmark."""
    _get_post(db, post_id)
    bookmarked = _toggle(db, PostBookmark, current_user.id, post_id)
    db.commit()
    return {"bookmarked": bookmarked}


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(CommunityPost).filter(
        CommunityPost.id == post_id,
        CommunityPost.user_id == current_user.id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not yours")
    db.query(PostLike).filter(PostLike.post_id == post_id).delete()
    db.query(PostBookmark).filter(PostBookmark.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}


@router.get("/stats")
def community_stats(db: Session = Depends(get_db)):
    """Sidebar data: member counts, trending tags this week, top contributors."""
    now = datetime.utcnow()
    # "Today" is the Indian calendar day; timestamps are stored in UTC.
    today_start = (now + IST_OFFSET).replace(hour=0, minute=0, second=0, microsecond=0) - IST_OFFSET

    members = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    states = db.query(func.count(func.distinct(User.state)))\
        .filter(User.state.isnot(None), User.state != "").scalar()
    posts_today = db.query(func.count(CommunityPost.id))\
        .filter(CommunityPost.created_at >= today_start).scalar()

    tag_counts, tag_names = Counter(), {}
    week_tags = db.query(CommunityPost.post_tags)\
        .filter(CommunityPost.created_at >= now - timedelta(days=7)).limit(1000).all()
    for (tags,) in week_tags:
        for t in tags or []:
            tag_names.setdefault(t.lower(), t)
        for key in {t.lower() for t in tags or []}:   # one count per post
            tag_counts[key] += 1

    contributors = db.query(User, func.count(CommunityPost.id).label("posts"))\
        .join(CommunityPost, CommunityPost.user_id == User.id)\
        .group_by(User.id).order_by(desc("posts")).limit(4).all()

    return {
        "members": members,
        "states": states,
        "posts_today": posts_today,
        "trending": [{"tag": tag_names[k], "posts": n} for k, n in tag_counts.most_common(5)],
        "top_contributors": [
            {"name": u.name, "location": u.district or u.state, "posts": n}
            for u, n in contributors
        ],
    }


def _get_post(db: Session, post_id: int) -> CommunityPost:
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def _toggle(db: Session, model, user_id: int, post_id: int) -> bool:
    """Add the row if missing, remove it if present. Returns the new state."""
    existing = db.query(model).filter(model.user_id == user_id, model.post_id == post_id).first()
    if existing:
        db.delete(existing)
        db.flush()
        return False
    try:
        db.add(model(user_id=user_id, post_id=post_id))
        db.flush()
    except IntegrityError:
        # A double click raced us and the row already exists.
        db.rollback()
    return True


def _posts_out(db: Session, posts: list, user: Optional[User]) -> list:
    if not posts:
        return []
    liked, bookmarked = set(), set()
    if user:
        ids = [p.id for p in posts]
        liked = {pid for (pid,) in db.query(PostLike.post_id)
                 .filter(PostLike.user_id == user.id, PostLike.post_id.in_(ids))}
        bookmarked = {pid for (pid,) in db.query(PostBookmark.post_id)
                      .filter(PostBookmark.user_id == user.id, PostBookmark.post_id.in_(ids))}
    return [
        _post_out(p, p.id in liked, p.id in bookmarked, user.id if user else None)
        for p in posts
    ]


def _post_out(post: CommunityPost, liked: bool = False, bookmarked: bool = False,
              user_id: Optional[int] = None) -> dict:
    author = post.user
    return {
        "id": post.id,
        "user_id": post.user_id,
        "author": author.name if author else "Farmer",
        "location": ", ".join(x for x in (author.district, author.state) if x) if author else None,
        "title": post.title,
        "body": post.body,
        "tag": post.tag,
        "emoji": post.emoji,
        "post_tags": post.post_tags or [],
        "likes": post.likes or 0,
        "comments": post.comments or 0,
        "liked": liked,
        "bookmarked": bookmarked,
        "is_mine": user_id is not None and post.user_id == user_id,
        "image_url": get_image_url(post.image_path) if post.image_path else None,
        "created_at": post.created_at.isoformat(),
    }
