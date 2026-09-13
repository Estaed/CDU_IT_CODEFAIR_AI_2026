"""The no-model comparison: TF-IDF word 1-2 grams and logistic regression, one classifier per
field, seeded. Scored with the same metric function as the extractor (PRD section 7).
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from fair_turn.core.constants import SEED


def fit_predict(train_texts: list[str], train_labels: list[str], texts: list[str]) -> list[str]:
    """Train on ``train_texts`` and return one predicted label per item of ``texts``."""
    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(max_iter=1000, random_state=SEED),
    )
    model.fit(train_texts, train_labels)
    return [str(label) for label in model.predict(texts)]
