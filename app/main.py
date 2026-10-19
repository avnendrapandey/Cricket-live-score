from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,HTTPException,Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from app.database import Base,engine,get_db
from app.models import Match
from app.cric_api import get_current_matches,get_matches_by_id

@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(
    title="cricket live score",
    lifespan=lifespan
)

app.mount("/static",StaticFiles(directory="app/static"),name="static")

templates=Jinja2Templates(directory="app/templates")

def save_matches(matches,db:Session):
    """Save or update API result in sql database."""

    for item in matches:
        match_id=item.get("id")

        if not match_id:
            continue

        values={
            "id":str(match_id),
            "name":item.get("name") or "cricket match",
            "match_type":item.get("matchtype"),
            "status":item.get("status"),
            "venue":item.get("venue"),
            "match_date":item.get("date"),
            "teams":item.get("teams",[]),
            "score":item.get("score",[])
        }

        existing=db.get(Match,str(match_id))

        if existing:
            for key, value in values.items():
                setattr(existing,key,value)
        else:
            db.add(Match(**values))
    db.commit()

@app.get("/",response_class=HTMLResponse)
def home(
    request:Request,
    db:Session=Depends(get_db)
):
    error=None
    matches=[]

    try:
        matches=get_current_matches()
        save_matches(matches,db)
    except Exception:
        error=(
            "live matches data is temporarly unavailable."
            "please try again shortly."
        )
        ##show previously showed matches if the api is unavailable
        matches=(
            db.query(Match)
            .order_by(Match.match_date.desc())
            .all()
        )
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "matches":matches,
            "error":error
        }
    )

@app.get("/match/{match_id}",response_class=HTMLResponse)
def match_detail(
    match_id:str,
    request:Request,
    db:Session=Depends(get_db)
):
    match=None
    error=None

    try:
        match=get_matches_by_id(match_id)
        if match:
            save_matches([match],db)
    except Exception:
        error="Unable to Refresh match information right now."
    if not match:
        match=db.get(Match,match_id)
    if not match:
        raise HTTPException(
            status_code=404,
            detail="match not found"
        )
    return templates.TemplateResponse(
        request=request,
        name="match_detail.html",
        context={
            "match":match,
            "error":error
        }
    )

@app.get("/api/matches")
def api_matches():
    """Return available matches as json."""

    try:
        return{
            "success":True,
            "matches":get_current_matches()
        }
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="cricket data provider is unavailable."
        )
    
@app.get("/api/matches/{match_id}")
def api_match_detail(match_id:str):
    """Return one available match as JSON."""

    try:
        match=get_matches_by_id(match_id)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="cricket data provider is unavailable."
        )
    if not match:
        raise HTTPException(
            status_code=404,
            detail="match not found"
        )
    return match

