import os
import time
import requests

from dotenv import load_dotenv
load_dotenv()

api_key=os.getenv("RAPIDAPI_KEY")
api_host="cricbuzz-cricket.p.rapidapi.com"
api_url=f"https://{api_host}/matches/v1/live"

_cache={
    "timestamp":0,
    "data":None
}
cache_seconds=60

def get_current_matches():
    """Fetch current matches with a 60 second cache"""
    if not api_key:
        raise RuntimeError(
            "cricket Api key is missing.Add it to your new env file."
        )
    now=time.time()

    if(
        _cache['data'] is not None and now -_cache["timestamp"]<cache_seconds
    ):
        return _cache['data']

    response=requests.get(
        api_url,
        headers={
            "X-RapidAPI-Key":api_key,
            "X-RapidAPI-Host":api_host,
        },
        timeout=20,
    )

    print("Rapidapi-Status",response.status_code)
    print("Rapidapi Response",response.text[:1000])

    response.raise_for_status()
    result=response.json()
    matches=[]

    for match_type in result.get("typeMatches",[]):
        print("Type Matches:",len(result.get("typeMatches",[])))
        for series in match_type.get("seriesMatches",[]):
            wrapper=series.get("seriesAdWrapper",{})

            for item in wrapper.get("matches",[]):
                info=item.get("matchInfo",{})
                score_info=item.get("matchScore",{})
                print("scoreinfo",score_info)

                match_id=info.get("matchId")

                if not match_id:
                    continue

                team1=info.get("team1",{})
                team2=info.get("team2",{})
                venue=info.get("venueInfo",{})

                teams=[
                    team1.get("teamName","Team1"),
                    team2.get("teamName","Team2"),
                ]
                scores=[]

                for key,team_name in [
                    ("team1Score",teams[0]),
                    ("team2Score",teams[1]),
                ]:
                    team_score=score_info.get(key,{})

                    if not isinstance (team_score,dict):
                        continue


                    for innings_key, innings in team_score.items():
                        if not isinstance(innings,dict):
                            continue


                        scores.append({
                            "inning":team_name,
                            "team":team_name,
                            "r":innings.get("runs",0),
                            "w":innings.get("wickets",0),
                            "o":innings.get("overs",0),
                        })

                matches.append({
                    "id":str(match_id),
                    "name":f"{teams[0]} vs {teams[1]}",
                    "matchtype":info.get("matchFormat","Cricket"),
                    "status":info.get('status',"status unavailable"),
                    "venue":venue.get("ground","Venue"),
                    "date":str(info.get("stardate","")),
                    "teams":teams,
                    "scores":scores
                })
                

    print("parsed matdches:",len(matches))

    _cache["timestamp"]=now
    _cache["data"]=matches

    return matches

def get_matches_by_id(match_id:str):
    """Find a match in currently available match list."""
    matches=get_current_matches()

    for match in matches:
        if str(match.get("id")) == str(match_id):
            return match
    return None

if __name__=="__main__":
    try:
        matches=get_current_matches()
        print("Total matches",len(matches))
        print("first match",matches[0] if matches else "No matches")
    except Exception as e:
        print("error",repr(e))
