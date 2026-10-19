from sqlalchemy import Column,String,DateTime,JSON
from sqlalchemy.sql import func
from app.database import Base

class Match(Base):
    __tablename__="matches"

    id=Column(String,primary_key=True,index=True)
    name=Column(String,nullable=False)
    match_type=Column(String,nullable=True)
    status=Column(String,nullable=True)
    venue=Column(String,nullable=True)
    match_date=Column(String,nullable=True)

    teams=Column(JSON,nullable=True)
    score=Column(JSON,nullable=True)

    updated_at=Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
