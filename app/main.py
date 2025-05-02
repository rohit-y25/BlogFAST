from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class BlogPostBase(BaseModel):
    title: Optional[str]
    content: Optional[str]
    published: Optional[bool] = True

class BlogPostCreate(BlogPostBase):
    title: str
    content: str

class BlogPostResponse(BlogPostBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Blog API")

@app.post("/posts/", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: BlogPostCreate, db: Session = Depends(get_db)):
    db_post = BlogPost(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts/", response_model=List[BlogPostResponse])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(BlogPost).offset(skip).limit(limit).all()

@app.get("/posts/{post_id}", response_model=BlogPostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=BlogPostResponse)
def update_post(post_id: int, post_data: BlogPostBase, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    for key, value in post_data.dict(exclude_unset=True).items():
        setattr(post, key, value)
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return post

@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Blogger"}
