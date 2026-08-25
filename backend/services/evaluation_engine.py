from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .nlp_processor import matching_phrases, normalize_text, tokenize, vocabulary_richness, word_count


def similarity_score(left: str, right: str) -> float:
    left_clean, right_clean = normalize_text(left), normalize_text(right)
    if not left_clean or not right_clean:
        return 0.0
    matrix = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit_transform([left_clean, right_clean])
    return round(float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0]) * 100, 2)


def keyword_coverage(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    normalized = normalize_text(text)
    hits = sum(1 for keyword in keywords if normalize_text(keyword) in normalized)
    return round((hits / len(keywords)) * 100, 2)


def word_count_score(text: str, minimum: int, maximum: int) -> float:
    count = word_count(text)
    if minimum <= count <= maximum:
        return 100.0
    if count < minimum:
        return round(max(0, (count / max(minimum, 1)) * 100), 2)
    return round(max(0, (maximum / max(count, 1)) * 100), 2)


def evaluate_submission(text: str, reference: str | None, keywords: list[str], minimum: int, maximum: int) -> dict[str, Any]:
    reference_similarity = similarity_score(text, reference or "")
    coverage = keyword_coverage(text, keywords)
    richness = vocabulary_richness(text)
    count_score = word_count_score(text, minimum, maximum)
    predicted = round((coverage * 0.30) + (reference_similarity * 0.30) + (min(richness, 100) * 0.15) + (count_score * 0.25), 2)
    feedback = []
    if coverage < 60:
        feedback.append("Add clearer coverage of the assignment's required concepts and keywords.")
    if reference and reference_similarity < 45:
        feedback.append("Strengthen the connection between the argument and the teacher-provided reference concepts.")
    if richness < 35:
        feedback.append("Use a wider range of precise vocabulary while keeping the writing coherent.")
    if count_score < 80:
        feedback.append("Review the required word-count range before submitting the final version.")
    if not feedback:
        feedback.append("The submission covers the measured criteria consistently. Review the detailed breakdown before final approval.")
    return {"predicted_score": predicted, "keyword_coverage": coverage, "reference_similarity": reference_similarity, "vocabulary_richness": richness, "word_count_score": count_score, "feedback": feedback, "word_count": word_count(text)}


def compare_submissions(text: str, others: list[tuple[int, str]], threshold: float) -> tuple[float, list[dict[str, Any]]]:
    matches = []
    for submission_id, other_text in others:
        score = similarity_score(text, other_text)
        if score / 100 >= threshold:
            matches.append({"compared_submission_id": submission_id, "similarity_score": score, "matching_phrases": matching_phrases(text, other_text)})
    risk = max((match["similarity_score"] for match in matches), default=0.0)
    return risk, matches
