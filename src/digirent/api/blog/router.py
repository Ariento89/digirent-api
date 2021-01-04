from datetime import date
from uuid import UUID
from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import or_, func
from typing import List, Optional
from digirent.api import dependencies as deps
from digirent.api.blog.schema import (
    BlogPostCreateSchema,
    BlogPostSchema,
    BlogPostUpdateSchema,
    TagSchema,
)
from digirent.database import models


router = APIRouter()


@router.get("/posts", response_model=List[BlogPostSchema])
def fetch_blog_posts(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tags: List[str] = Query(None),
    session: Session = Depends(deps.get_database_session),
):
    offset = (page - 1) * page_size
    limit = page_size
    posts_query = session.query(models.BlogPost)
    if start_date:
        posts_query = posts_query.filter(
            or_(
                func.DATE(models.BlogPost.created_at) >= start_date,
                func.DATE(models.BlogPost.updated_at) >= start_date,
            )
        )
    if end_date:
        posts_query = posts_query.filter(
            or_(
                func.DATE(models.BlogPost.created_at) <= start_date,
                func.DATE(models.BlogPost.updated_at) <= start_date,
            )
        )
    # TODO implement search
    if tags:
        for tag in tags:
            blog_tag: models.BlogTag = session.query(models.BlogTag).get(tag)
            if blog_tag:
                posts_query = posts_query.filter(
                    models.BlogPost.tags.contains(blog_tag)
                )
    return posts_query.offset(offset).limit(limit).all()


@router.get("/posts/{post_id}", response_model=BlogPostSchema)
def get_single_blog_post(
    post_id: UUID, session: Session = Depends(deps.get_database_session)
):
    post: models.BlogPost = session.query(models.BlogPost).get(post_id)
    if not post:
        raise HTTPException(404, "Not found")
    return post


@router.get("/tags", response_model=List[TagSchema])
def get_all_blog_tags(session: Session = Depends(deps.get_database_session)):
    return session.query(models.BlogTag).all()


@router.post("/posts", response_model=BlogPostSchema)
def create_new_blog_post(
    data: BlogPostCreateSchema,
    session: Session = Depends(deps.get_database_session),
    _: models.Admin = Depends(deps.get_current_admin_user),
):
    current_blog_post_with_same_title = (
        session.query(models.BlogPost)
        .filter(func.lower(models.BlogPost.title) == data.title.lower())
        .one_or_none()
    )
    if current_blog_post_with_same_title:
        raise HTTPException(400, "Blog post with same title already exists")
    blog_tags = []
    for tag in data.tags:
        blog_tag = session.query(models.BlogTag).get(tag)
        if not blog_tag:
            blog_tag = models.BlogTag(name=tag)
        blog_tags.append(blog_tag)
    post: models.BlogPost = models.BlogPost(
        title=data.title, content=data.content, tags=blog_tags
    )
    session.add(post)
    session.commit()
    return post


@router.put("/posts/{post_id}", response_model=BlogPostSchema)
def update_blog_post(
    post_id: UUID,
    data: BlogPostUpdateSchema,
    session: Session = Depends(deps.get_database_session),
    _: models.Admin = Depends(deps.get_current_admin_user),
):
    post: models.BlogPost = session.query(models.BlogPost).get(post_id)
    if not post:
        raise HTTPException(404, "Not found")
    current_blog_post_with_same_title = (
        session.query(models.BlogPost)
        .filter(models.BlogPost.title == data.title.lower())
        .one_or_none()
    )
    if (
        current_blog_post_with_same_title
        and current_blog_post_with_same_title.id != post.id
    ):
        raise HTTPException(400, "Blog post with same title already exists")
    blog_tags = []
    for tag in data.tags:
        blog_tag = session.query(models.BlogTag).get(tag)
        if not blog_tag:
            blog_tag = models.BlogTag(name=tag)
        blog_tags.append(blog_tag)
    post.tags = blog_tags
    post.title = data.title
    post.content = data.content
    session.commit()
    return post
