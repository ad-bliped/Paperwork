from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Paperwork API", version="0.1.0")


class TopicRequest(BaseModel):
    user_id: str
    topics: list[str] = Field(default_factory=list)


class EmailPreferences(BaseModel):
    user_id: str
    send_time: str = "07:00"
    timezone: str = "Asia/Seoul"
    frequency: Literal["daily", "weekdays"] = "daily"
    enabled: bool = True


class WritingSectionPatch(BaseModel):
    current_words: int = Field(ge=0)
    target_words: int = Field(gt=0)


class WritingProjectCreate(BaseModel):
    user_id: str
    title: str
    sections: dict[str, int] = Field(
        default_factory=lambda: {
            "서론": 800,
            "선행연구": 1200,
            "방법": 1200,
            "결과": 1200,
            "논의": 1000,
        }
    )


class InMemoryStore:
    def __init__(self) -> None:
        self.user_topics: dict[str, list[str]] = {}
        self.email_preferences: dict[str, EmailPreferences] = {}
        self.writing_projects: dict[str, dict] = {}
        self.reminder_logs: list[dict] = []
        self.email_delivery_logs: list[dict] = []
        self.papers = [
            {
                "id": "p1",
                "title": "청소년 스마트폰 사용과 수면의 질 관계 연구",
                "authors": "김OO 외",
                "journal": "한국청소년연구",
                "year": 2024,
                "keywords": ["청소년", "스마트폰", "수면"],
                "type": "배경",
            },
            {
                "id": "p2",
                "title": "혼합연구 설계 방법론의 실제 적용",
                "authors": "이OO",
                "journal": "교육방법연구",
                "year": 2023,
                "keywords": ["방법론", "혼합연구", "연구설계"],
                "type": "방법",
            },
            {
                "id": "p3",
                "title": "직장인 대학원생의 시간관리 전략과 성과",
                "authors": "박OO 외",
                "journal": "성인학습연구",
                "year": 2022,
                "keywords": ["시간관리", "직장인", "대학원"],
                "type": "논의",
            },
            {
                "id": "p4",
                "title": "딥러닝 기반 추천 시스템의 개인화 성능 분석",
                "authors": "정OO",
                "journal": "정보과학논총",
                "year": 2024,
                "keywords": ["추천", "개인화", "딥러닝"],
                "type": "방법",
            },
        ]


store = InMemoryStore()


def _find_low_progress_section(user_id: str) -> str | None:
    projects = [p for p in store.writing_projects.values() if p["user_id"] == user_id]
    if not projects:
        return None
    lowest = None
    lowest_ratio = 10.0
    for project in projects:
        for section_name, section in project["sections"].items():
            ratio = section["current_words"] / section["target_words"]
            if ratio < lowest_ratio:
                lowest_ratio = ratio
                lowest = section_name
    return lowest


def _section_to_paper_type(section: str | None) -> str | None:
    if not section:
        return None
    mapping = {
        "서론": "배경",
        "선행연구": "배경",
        "방법": "방법",
        "결과": "방법",
        "논의": "논의",
    }
    return mapping.get(section)


def _recommend_for_user(user_id: str, count: int = 3) -> list[dict]:
    topics = set(store.user_topics.get(user_id, []))
    preferred_type = _section_to_paper_type(_find_low_progress_section(user_id))

    def score(paper: dict) -> tuple[int, int, int]:
        topic_overlap = len(topics.intersection(set(paper["keywords"])))
        section_boost = 2 if preferred_type and paper["type"] == preferred_type else 0
        recency = paper["year"]
        return (section_boost, topic_overlap, recency)

    ranked = sorted(store.papers, key=score, reverse=True)
    top = ranked[:count]

    results = []
    for p in top:
        reasons = []
        overlap = topics.intersection(set(p["keywords"]))
        if overlap:
            reasons.append(f"관심 주제 일치: {', '.join(sorted(overlap))}")
        if preferred_type and p["type"] == preferred_type:
            reasons.append("집필 미완료 섹션 보강에 적합")
        if p["year"] >= datetime.now().year - 1:
            reasons.append("최신 논문")
        if not reasons:
            reasons.append("탐색 다양성 확보")

        results.append({
            "paper_id": p["id"],
            "title": p["title"],
            "authors": p["authors"],
            "journal": p["journal"],
            "year": p["year"],
            "reason": " / ".join(reasons),
            "deep_link": f"paperwork://papers/{p['id']}",
        })
    return results


@app.post("/users/topics")
def set_topics(payload: TopicRequest) -> dict:
    store.user_topics[payload.user_id] = payload.topics
    return {"user_id": payload.user_id, "topics": payload.topics}


@app.put("/users/email-preferences")
def set_email_preferences(payload: EmailPreferences) -> dict:
    store.email_preferences[payload.user_id] = payload
    return payload.model_dump()


@app.post("/writing-projects")
def create_writing_project(payload: WritingProjectCreate) -> dict:
    project_id = str(uuid4())
    store.writing_projects[project_id] = {
        "id": project_id,
        "user_id": payload.user_id,
        "title": payload.title,
        "sections": {
            name: {"target_words": target, "current_words": 0}
            for name, target in payload.sections.items()
        },
    }
    return store.writing_projects[project_id]


@app.patch("/writing-projects/{project_id}/sections/{section_id}")
def patch_writing_section(project_id: str, section_id: str, payload: WritingSectionPatch) -> dict:
    project = store.writing_projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if section_id not in project["sections"]:
        raise HTTPException(status_code=404, detail="Section not found")

    project["sections"][section_id] = {
        "target_words": payload.target_words,
        "current_words": payload.current_words,
    }
    return {"project_id": project_id, "section_id": section_id, **project["sections"][section_id]}


@app.get("/papers/recommendations/today")
def today_recommendations(user_id: str = Query(...)) -> dict:
    return {"user_id": user_id, "recommendations": _recommend_for_user(user_id)}


@app.get("/users/daily-digest/preview")
def digest_preview(user_id: str = Query(...)) -> dict:
    prefs = store.email_preferences.get(user_id)
    recommendations = _recommend_for_user(user_id)
    return {
        "user_id": user_id,
        "send_time": prefs.send_time if prefs else "07:00",
        "timezone": prefs.timezone if prefs else "Asia/Seoul",
        "subject": "[Paperwork] 오늘의 추천 논문",
        "recommendations": recommendations,
    }


@app.post("/jobs/send-daily-paper-email")
def send_daily_digest() -> dict:
    sent_count = 0
    for user_id in store.user_topics:
        prefs = store.email_preferences.get(user_id)
        if prefs and not prefs.enabled:
            continue
        payload = {
            "user_id": user_id,
            "sent_at": datetime.utcnow().isoformat(),
            "recommendation_ids": [r["paper_id"] for r in _recommend_for_user(user_id)],
            "status": "sent",
        }
        store.email_delivery_logs.append(payload)
        sent_count += 1
    return {"sent": sent_count, "logs": store.email_delivery_logs[-sent_count:] if sent_count else []}


@app.post("/jobs/generate-reminders")
def generate_reminders() -> dict:
    created = []
    for project in store.writing_projects.values():
        user_id = project["user_id"]
        for section_name, section in project["sections"].items():
            ratio = section["current_words"] / section["target_words"]
            if ratio < 0.7:
                reminder = {
                    "user_id": user_id,
                    "type": "goal_shortfall",
                    "message": f"{section_name} 섹션 진행률이 낮습니다. 오늘 300자 보강을 권장합니다.",
                    "created_at": datetime.utcnow().isoformat(),
                }
                store.reminder_logs.append(reminder)
                created.append(reminder)
                break
    return {"created": len(created), "reminders": created}


@app.get("/users/reminders/today")
def get_reminders_today(user_id: str = Query(...)) -> dict:
    reminders = [r for r in store.reminder_logs if r["user_id"] == user_id]
    return {"user_id": user_id, "reminders": reminders}
