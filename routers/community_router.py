from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from database import get_db
from models import User, CommunityPost
from auth import get_current_user
from services.image_service import save_image

router = APIRouter(prefix="/community", tags=["community"])

@router.get("/posts")
def get_posts(
    skip: int = 0,
    limit: int = 20,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(CommunityPost)
    if tag and tag != "All":
        q = q.filter(CommunityPost.tag == tag)
    if search:
        q = q.filter(
            CommunityPost.title.ilike(f"%{search}%") |
            CommunityPost.body.ilike(f"%{search}%")
        )
    posts = q.order_by(CommunityPost.created_at.desc()).offset(skip).limit(limit).all()
    return [_post_out(p) for p in posts]

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
    import json
    if len(title) < 5:
        raise HTTPException(status_code=400, detail="Title too short")
    if len(body) < 20:
        raise HTTPException(status_code=400, detail="Body too short")

    image_path = None
    if image:
        image_bytes = await image.read()
        image_path = save_image(image_bytes, prefix="post")

    post = CommunityPost(
        user_id=current_user.id,
        title=title,
        body=body,
        tag=tag,
        emoji=emoji,
        post_tags=json.loads(post_tags),
        image_path=image_path,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _post_out(post)

@router.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes += 1
    db.commit()
    return {"likes": post.likes}

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
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}

def _post_out(post: CommunityPost) -> dict:
    return {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "body": post.body,
        "tag": post.tag,
        "emoji": post.emoji,
        "post_tags": post.post_tags or [],
        "likes": post.likes,
        "comments": post.comments,
        "image_url": f"/uploads/{post.image_path.split('/')[-1]}" if post.image_path else None,
        "created_at": post.created_at.isoformat(),
    }