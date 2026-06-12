"""Prediction extractor.

Hybrid approach:
  Layer 1 – Rule-based: regex patterns for scores, team names, confidence phrases.
  Layer 2 – LLM (optional): structured extraction via OpenAI / local model.
             Enabled via config.llm_enabled = true.

TODO (LLM layer):
  1. Set OPENAI_API_KEY env var and llm.enabled=true in settings.yml.
  2. Implement _extract_llm() using the OpenAI client.
  3. The prompt template is in _LLM_PROMPT below.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Optional

from app.models.domain import (
    Prediction,
    PredictionItem,
    PredictionType,
)
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Known team name lists (extend as needed)
# ---------------------------------------------------------------------------
_TEAMS_FR = [
    "france", "brésil", "bresil", "argentina", "argentine", "allemagne", "germany",
    "espagne", "spain", "angleterre", "england", "portugal", "belgique", "belgium",
    "pays-bas", "netherlands", "hollande", "italie", "italy", "croatie", "croatia",
    "maroc", "morocco", "sénégal", "senegal", "usa", "états-unis", "etats-unis",
    "mexique", "mexico", "canada", "japon", "japan", "corée", "korea",
]
_TEAMS_EN = [
    "france", "brazil", "argentina", "germany", "spain", "england", "portugal",
    "belgium", "netherlands", "holland", "italy", "croatia", "morocco", "senegal",
    "usa", "united states", "mexico", "canada", "japan", "south korea", "australia",
    "uruguay", "colombia", "ecuador", "chile", "switzerland", "poland",
]
_TEAMS_ES = [
    "france", "francia", "brasil", "argentina", "alemania", "españa", "inglaterra",
    "portugal", "bélgica", "belgica", "países bajos", "holanda", "italia", "croacia",
    "marruecos", "senegal", "estados unidos", "méxico", "canada", "japón", "corea",
]

ALL_TEAMS = sorted(set(_TEAMS_FR + _TEAMS_EN + _TEAMS_ES), key=len, reverse=True)

# Regex for exact score patterns: "2-1", "2 - 1", "2:1"
_SCORE_RE = re.compile(r"\b(\d{1,2})\s*[-:]\s*(\d{1,2})\b")

# Confidence phrases mapped to approximate floats
_CONFIDENCE_PHRASES: dict[str, float] = {
    "certain": 0.95, "sûr": 0.95, "sure": 0.95, "seguro": 0.95,
    "très confiant": 0.85, "very confident": 0.85, "muy confiado": 0.85,
    "confiant": 0.75, "confident": 0.75, "confiado": 0.75,
    "pense que": 0.65, "think": 0.65, "creo": 0.65,
    "peut-être": 0.45, "maybe": 0.45, "quizás": 0.45,
    "surprise": 0.35, "upset": 0.35,
}

_LLM_PROMPT = """
You are a football prediction analyst. Given the following transcript of a YouTube video,
extract structured predictions about the 2026 FIFA World Cup.

Return a JSON object with:
{
  "tournament_winner": "<team or null>",
  "key_arguments": ["<argument1>", ...],
  "key_quotes": ["<exact quote>", ...],
  "overall_confidence": <0.0-1.0 or null>,
  "items": [
    {
      "prediction_type": "<tournament_winner|match_winner|exact_score|qualified_team|dark_horse|...>",
      "team": "<team or null>",
      "opponent": "<team or null>",
      "score_team": <int or null>,
      "score_opponent": <int or null>,
      "stage": "<group|round_of_16|quarter_final|semi_final|final or null>",
      "confidence": <0.0-1.0 or null>,
      "raw_text": "<supporting quote>"
    }
  ]
}

Transcript:
{transcript}
"""


def extract_predictions(
    transcript_text: str,
    video_id: str,
    channel_id: str,
    language: str = "en",
) -> Prediction:
    """Extract predictions from a transcript.

    Tries LLM extraction first (if enabled), then falls back to rule-based.
    """
    if config.llm_enabled and config.llm_api_key:
        try:
            return _extract_llm(transcript_text, video_id, channel_id)
        except Exception as exc:
            logger.warning(f"LLM extraction failed, falling back to rules: {exc}")

    return _extract_rules(transcript_text, video_id, channel_id, language)


# ---------------------------------------------------------------------------
# Rule-based extraction
# ---------------------------------------------------------------------------


def _extract_rules(
    text: str,
    video_id: str,
    channel_id: str,
    language: str = "en",
) -> Prediction:
    text_lower = text.lower()
    items: list[PredictionItem] = []

    # --- Tournament winner ---
    winner = _detect_tournament_winner(text_lower)
    if winner:
        items.append(
            PredictionItem(
                prediction_type=PredictionType.TOURNAMENT_WINNER,
                team=winner,
                confidence=_detect_confidence(text_lower),
                raw_text=_find_sentence_with(text, winner),
            )
        )

    # --- Exact scores ---
    items.extend(_detect_exact_scores(text, text_lower))

    # --- Dark horses ---
    items.extend(_detect_dark_horses(text, text_lower))

    # --- Qualified / group stage mentions ---
    items.extend(_detect_qualified(text, text_lower))

    overall_conf = _detect_confidence(text_lower)
    key_args = _extract_key_arguments(text)

    return Prediction(
        video_id=video_id,
        channel_id=channel_id,
        tournament_winner=winner,
        key_arguments=key_args,
        key_quotes=_extract_key_quotes(text),
        overall_confidence=overall_conf,
        items=items,
        extracted_at=datetime.now(tz=timezone.utc),
    )


def _detect_tournament_winner(text_lower: str) -> Optional[str]:
    winner_patterns = [
        r"(?:vainqueur|gagne|champion|winner|campeón|ganador)(?:\s+\w+){0,4}\s+(?:sera|will be|será|est)\s+(?:la\s+|le\s+|l[\''])?(\w+)",
        r"(\w+)\s+(?:va gagner|will win|ganará|gagnera)\s+(?:le\s+)?(?:mondial|world cup|copa del mundo|tournoi|tournament)",
        r"(?:je\s+)?(?:pense|crois|believe|think|creo)\s+que\s+(?:la\s+|le\s+)?(\w+)",
    ]
    for pattern in winner_patterns:
        m = re.search(pattern, text_lower)
        if m:
            candidate = m.group(1).strip()
            matched = _match_team(candidate)
            if matched:
                return matched
    return None


def _detect_exact_scores(text: str, text_lower: str) -> list[PredictionItem]:
    items = []
    for m in _SCORE_RE.finditer(text_lower):
        # Look for team names around the score
        start = max(0, m.start() - 60)
        end = min(len(text_lower), m.end() + 60)
        context = text_lower[start:end]
        teams_found = [t for t in ALL_TEAMS if t in context]
        if len(teams_found) >= 2:
            items.append(
                PredictionItem(
                    prediction_type=PredictionType.EXACT_SCORE,
                    team=_canonical(teams_found[0]),
                    opponent=_canonical(teams_found[1]),
                    score_team=int(m.group(1)),
                    score_opponent=int(m.group(2)),
                    raw_text=text[start:end].strip(),
                )
            )
    return items


def _detect_dark_horses(text: str, text_lower: str) -> list[PredictionItem]:
    patterns = [
        r"dark horse[s]?\s*[:\-–]?\s*(\w+)",
        r"surprise\s+(?:du\s+tournoi\s+)?[:\-–]?\s*(\w+)",
        r"(\w+)\s+(?:peut|could|puede)\s+créer\s+la\s+surprise",
        r"(?:équipe\s+surprise|sleeper\s+team|equipo\s+sorpresa)[:\s]+(\w+)",
    ]
    items = []
    for pat in patterns:
        for m in re.finditer(pat, text_lower):
            candidate = m.group(1).strip()
            team = _match_team(candidate)
            if team:
                items.append(
                    PredictionItem(
                        prediction_type=PredictionType.DARK_HORSE,
                        team=team,
                        raw_text=_find_sentence_with(text, candidate),
                    )
                )
    return items


def _detect_qualified(text: str, text_lower: str) -> list[PredictionItem]:
    patterns = [
        r"(\w+)\s+(?:va se qualifier|will qualify|se qualificará|qualifié)",
        r"qualifié[s]?\s+[:\-–]?\s*(\w+)",
    ]
    items = []
    for pat in patterns:
        for m in re.finditer(pat, text_lower):
            candidate = m.group(1).strip()
            team = _match_team(candidate)
            if team:
                items.append(
                    PredictionItem(
                        prediction_type=PredictionType.QUALIFIED_TEAM,
                        team=team,
                        raw_text=_find_sentence_with(text, candidate),
                    )
                )
    return items


def _detect_confidence(text_lower: str) -> Optional[float]:
    for phrase, score in sorted(_CONFIDENCE_PHRASES.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in text_lower:
            return score
    # Look for explicit percentage: "80%", "80 %"
    m = re.search(r"\b(\d{2,3})\s*%", text_lower)
    if m:
        pct = int(m.group(1))
        if 0 <= pct <= 100:
            return pct / 100
    return None


def _extract_key_arguments(text: str) -> list[str]:
    """Extract sentences that look like arguments."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    keywords = ["parce que", "because", "porque", "donc", "so", "así que",
                 "grâce à", "thanks to", "gracias a", "malgré", "despite",
                 "meilleur", "best", "mejor", "rang", "ranked"]
    return [s.strip() for s in sentences if any(k in s.lower() for k in keywords)][:5]


def _extract_key_quotes(text: str) -> list[str]:
    """Extract short, impactful sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if 20 < len(s) < 150][:5]


def _match_team(candidate: str) -> Optional[str]:
    """Return canonical team name if candidate matches a known team."""
    for team in ALL_TEAMS:
        if candidate.lower() == team or candidate.lower().startswith(team):
            return _canonical(team)
    return None


def _canonical(team: str) -> str:
    """Return a standardised English team name."""
    mapping = {
        "france": "France", "brésil": "Brazil", "bresil": "Brazil", "brasil": "Brazil",
        "argentina": "Argentina", "argentine": "Argentina",
        "allemagne": "Germany", "germany": "Germany",
        "espagne": "Spain", "spain": "Spain", "españa": "Spain",
        "angleterre": "England", "england": "England", "inglaterra": "England",
        "portugal": "Portugal",
        "belgique": "Belgium", "belgium": "Belgium", "bélgica": "Belgium",
        "pays-bas": "Netherlands", "netherlands": "Netherlands",
        "hollande": "Netherlands", "holanda": "Netherlands",
        "italie": "Italy", "italy": "Italy", "italia": "Italy",
        "croatie": "Croatia", "croatia": "Croatia", "croacia": "Croatia",
        "maroc": "Morocco", "morocco": "Morocco", "marruecos": "Morocco",
        "sénégal": "Senegal", "senegal": "Senegal",
        "usa": "USA", "états-unis": "USA", "etats-unis": "USA",
        "united states": "USA", "estados unidos": "USA",
        "mexique": "Mexico", "mexico": "Mexico", "méxico": "Mexico",
        "canada": "Canada",
        "japon": "Japan", "japan": "Japan", "japón": "Japan",
        "corée": "South Korea", "korea": "South Korea", "corea": "South Korea",
    }
    return mapping.get(team.lower(), team.capitalize())


def _find_sentence_with(text: str, keyword: str) -> str:
    """Return the first sentence containing keyword."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for s in sentences:
        if keyword.lower() in s.lower():
            return s.strip()
    return ""


# ---------------------------------------------------------------------------
# LLM extraction (optional)
# ---------------------------------------------------------------------------


def _extract_llm(text: str, video_id: str, channel_id: str) -> Prediction:  # pragma: no cover
    """Extract predictions using an LLM.

    TODO: Implement using openai library:
        import openai
        client = openai.OpenAI(api_key=config.llm_api_key)
        response = client.chat.completions.create(
            model=config.llm_model,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": _LLM_PROMPT.format(transcript=text[:8000])}],
            max_tokens=config.get("llm", "max_tokens", default=2000),
        )
        raw = json.loads(response.choices[0].message.content)
        return _parse_llm_response(raw, video_id, channel_id)
    """
    raise NotImplementedError("LLM extraction not yet implemented.")


def _parse_llm_response(raw: dict, video_id: str, channel_id: str) -> Prediction:  # pragma: no cover
    items = [
        PredictionItem(
            prediction_type=PredictionType(i.get("prediction_type", "other")),
            team=i.get("team"),
            opponent=i.get("opponent"),
            score_team=i.get("score_team"),
            score_opponent=i.get("score_opponent"),
            stage=i.get("stage"),
            confidence=i.get("confidence"),
            raw_text=i.get("raw_text"),
        )
        for i in raw.get("items", [])
    ]
    return Prediction(
        video_id=video_id,
        channel_id=channel_id,
        tournament_winner=raw.get("tournament_winner"),
        key_arguments=raw.get("key_arguments", []),
        key_quotes=raw.get("key_quotes", []),
        overall_confidence=raw.get("overall_confidence"),
        items=items,
        extracted_at=datetime.now(tz=timezone.utc),
    )
