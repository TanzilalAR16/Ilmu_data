import pickle
import re
from fastapi import FastAPI
from pydantic import BaseModel
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer

# Download required NLTK data
nltk.download('stopwords')

app = FastAPI()

# Load the saved model and CountVectorizer
model_filename = 'ensemble_model.pkl'
with open(model_filename, 'rb') as file:
    loaded_model = pickle.load(file)

cv_filename = 'cv.pkl'
with open(cv_filename, 'rb') as file:
    loaded_cv = pickle.load(file)

class Review(BaseModel):
    review: str

@app.post("/predict_sentiment")
async def predict_sentiment(review: Review):
    # Preprocess the input text
    text = review.review
    word = re.sub('[^a-zA-Z]', ' ', text)
    word = word.lower()
    word = word.split()
    ps = PorterStemmer()
    all_stopwords = stopwords.words('indonesian')
    word = [ps.stem(w) for w in word if not w in set(all_stopwords)]
    word = ' '.join(word)

    # Transform the text using the loaded CountVectorizer
    X_new = loaded_cv.transform([word]).toarray()

    # Make the prediction
    y_new_pred = loaded_model.predict(X_new)[0]

    sentiment_mapping = {1: "Negative", 2: "Neutral", 3: "Positive"}
    sentiment = sentiment_mapping[y_new_pred]
    return {"sentiment": sentiment}