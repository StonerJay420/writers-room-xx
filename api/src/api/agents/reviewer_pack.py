"""Reviewer Pack agent for multi-perspective critique as specified in Prompt 72."""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class ReviewerPerspective(BaseModel):
    """A single reviewer's perspective."""
    reviewer_type: str  # "literary", "commercial", "reader", "academic", "genre"
    rating: float  # 0-5 stars
    strengths: List[str]
    weaknesses: List[str]
    key_feedback: str
    would_recommend: bool


class ReviewerPackResult(BaseModel):
    """Schema for Reviewer Pack output."""
    reviews: List[ReviewerPerspective]
    consensus_strengths: List[str]
    consensus_weaknesses: List[str]
    average_rating: float
    marketability_score: float
    literary_merit_score: float
    recommendations: List[str]
    rationale: List[str]


async def run_reviewer_pack(
    scene_text: str,
    genre: str = "literary fiction",
    target_audience: str = "adult",
    edge_intensity: int = 1,
    model: str = "anthropic/claude-3-opus"
) -> Dict[str, Any]:
    """
    Run Reviewer Pack for multi-perspective critique.
    
    Simulates feedback from different reviewer types:
    - Literary critic (prose quality, themes)
    - Commercial editor (marketability, pace)
    - Target reader (engagement, emotion)
    - Academic reviewer (structure, craft)
    - Genre specialist (conventions, expectations)
    
    Args:
        scene_text: The scene text to review
        genre: Genre of the work
        target_audience: Target demographic
        edge_intensity: 0-3 for how harsh reviews should be
        model: LLM model to use
        
    Returns:
        Dictionary with multi-perspective reviews and consensus
    """
    reviews = []
    
    # Literary critic perspective
    literary_review = _generate_literary_review(scene_text, edge_intensity)
    reviews.append(literary_review)
    
    # Commercial editor perspective
    commercial_review = _generate_commercial_review(scene_text, genre, edge_intensity)
    reviews.append(commercial_review)
    
    # Target reader perspective
    reader_review = _generate_reader_review(scene_text, target_audience, edge_intensity)
    reviews.append(reader_review)
    
    # Academic reviewer perspective
    academic_review = _generate_academic_review(scene_text, edge_intensity)
    reviews.append(academic_review)
    
    # Genre specialist perspective
    genre_review = _generate_genre_review(scene_text, genre, edge_intensity)
    reviews.append(genre_review)
    
    # Find consensus
    all_strengths = []
    all_weaknesses = []
    for review in reviews:
        all_strengths.extend(review.strengths)
        all_weaknesses.extend(review.weaknesses)
    
    # Find most common strengths/weaknesses
    consensus_strengths = list(set(s for s in all_strengths if all_strengths.count(s) >= 2))[:3]
    consensus_weaknesses = list(set(w for w in all_weaknesses if all_weaknesses.count(w) >= 2))[:3]
    
    # Calculate scores
    average_rating = sum(r.rating for r in reviews) / len(reviews)
    marketability_score = commercial_review.rating / 5.0
    literary_merit_score = literary_review.rating / 5.0
    
    # Generate recommendations
    recommendations = []
    if average_rating < 3:
        recommendations.append("Major revision needed - fundamental issues across perspectives")
    elif average_rating < 4:
        recommendations.append("Moderate revision - address consensus weaknesses")
    else:
        recommendations.append("Minor polish - strong foundation, refine details")
    
    if marketability_score < 0.6:
        recommendations.append("Enhance commercial appeal - consider pace and hooks")
    
    if literary_merit_score < 0.6:
        recommendations.append("Strengthen prose and thematic depth")
    
    # Build rationale
    rationale = [
        f"Gathered {len(reviews)} distinct reviewer perspectives",
        f"Average rating: {average_rating:.1f}/5 stars",
        f"Found {len(consensus_strengths)} consensus strengths and {len(consensus_weaknesses)} consensus weaknesses"
    ]
    
    result = ReviewerPackResult(
        reviews=reviews,
        consensus_strengths=consensus_strengths,
        consensus_weaknesses=consensus_weaknesses,
        average_rating=average_rating,
        marketability_score=marketability_score,
        literary_merit_score=literary_merit_score,
        recommendations=recommendations,
        rationale=rationale
    )
    
    return result.model_dump()


def _generate_literary_review(text: str, intensity: int) -> ReviewerPerspective:
    """Generate literary critic review."""
    word_count = len(text.split())
    has_metaphor = "like" in text or "as if" in text
    
    strengths = []
    weaknesses = []
    
    if has_metaphor:
        strengths.append("Uses figurative language")
    if word_count > 500:
        strengths.append("Substantial scene development")
    
    if not has_metaphor:
        weaknesses.append("Lacks figurative language")
    if word_count < 200:
        weaknesses.append("Underdeveloped scene")
    
    rating = 3.5 - (intensity * 0.5)
    
    return ReviewerPerspective(
        reviewer_type="literary",
        rating=max(1, rating),
        strengths=strengths or ["Competent prose"],
        weaknesses=weaknesses or ["Could push boundaries more"],
        key_feedback="Focus on elevating prose beyond functional to artistic",
        would_recommend=rating >= 3
    )


def _generate_commercial_review(text: str, genre: str, intensity: int) -> ReviewerPerspective:
    """Generate commercial editor review."""
    has_dialogue = '"' in text
    has_conflict = any(word in text.lower() for word in ["but", "however", "conflict", "problem"])
    
    strengths = []
    weaknesses = []
    
    if has_dialogue:
        strengths.append("Good dialogue presence")
    if has_conflict:
        strengths.append("Clear conflict/tension")
    
    if len(text.split('\n\n')[0]) > 200:
        weaknesses.append("Opening paragraph too long")
    if not has_dialogue:
        weaknesses.append("Needs more dialogue")
    
    rating = 3.5 - (intensity * 0.3)
    
    return ReviewerPerspective(
        reviewer_type="commercial",
        rating=max(1, rating),
        strengths=strengths or ["Shows market awareness"],
        weaknesses=weaknesses or ["Could be more commercial"],
        key_feedback=f"Consider {genre} market expectations for pacing",
        would_recommend=rating >= 3.5
    )


def _generate_reader_review(text: str, audience: str, intensity: int) -> ReviewerPerspective:
    """Generate target reader review."""
    emotional_words = ["felt", "heart", "tears", "smiled", "laughed", "feared"]
    has_emotion = any(word in text.lower() for word in emotional_words)
    
    strengths = []
    weaknesses = []
    
    if has_emotion:
        strengths.append("Emotionally engaging")
    if len(text.split('.')) > 10:
        strengths.append("Good scene length")
    
    if not has_emotion:
        weaknesses.append("Lacks emotional connection")
    
    rating = 4.0 - (intensity * 0.4)
    
    return ReviewerPerspective(
        reviewer_type="reader",
        rating=max(1, rating),
        strengths=strengths or ["Readable and clear"],
        weaknesses=weaknesses or ["Could connect more emotionally"],
        key_feedback=f"As a {audience} reader, I want more emotional stakes",
        would_recommend=rating >= 3
    )


def _generate_academic_review(text: str, intensity: int) -> ReviewerPerspective:
    """Generate academic reviewer perspective."""
    sentences = text.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    
    strengths = []
    weaknesses = []
    
    if 15 <= avg_sentence_length <= 20:
        strengths.append("Good sentence variation")
    if len(set(text.split('\n\n'))) > 3:
        strengths.append("Strong paragraph structure")
    
    if avg_sentence_length > 25:
        weaknesses.append("Sentences too complex")
    elif avg_sentence_length < 10:
        weaknesses.append("Sentences too simple")
    
    rating = 3.0 - (intensity * 0.3)
    
    return ReviewerPerspective(
        reviewer_type="academic",
        rating=max(1, rating),
        strengths=strengths or ["Demonstrates craft awareness"],
        weaknesses=weaknesses or ["Could show more technical mastery"],
        key_feedback="Consider narrative structure and technique",
        would_recommend=rating >= 3
    )


def _generate_genre_review(text: str, genre: str, intensity: int) -> ReviewerPerspective:
    """Generate genre specialist review."""
    genre_expectations = {
        "fantasy": ["magic", "world", "quest"],
        "romance": ["love", "heart", "kiss"],
        "thriller": ["danger", "chase", "time"],
        "literary fiction": ["meaning", "truth", "human"]
    }
    
    expected_words = genre_expectations.get(genre.lower(), [])
    matches = sum(1 for word in expected_words if word in text.lower())
    
    strengths = []
    weaknesses = []
    
    if matches >= 2:
        strengths.append(f"Fits {genre} conventions")
    if matches < 1:
        weaknesses.append(f"Doesn't feel like {genre}")
    
    rating = 3.5 - (intensity * 0.3) + (matches * 0.2)
    
    return ReviewerPerspective(
        reviewer_type="genre",
        rating=max(1, min(5, rating)),
        strengths=strengths or [f"Shows understanding of {genre}"],
        weaknesses=weaknesses or [f"Could lean more into {genre} elements"],
        key_feedback=f"Genre readers expect certain {genre} elements",
        would_recommend=rating >= 3
    )