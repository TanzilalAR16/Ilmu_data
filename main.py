import pickle
import re
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import nltk

# Download required NLTK data
nltk.download('stopwords')

app = FastAPI()

# Serve static files (HTML, CSS, JS)
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Load the saved model and CountVectorizer
model_filename = 'ensemble_model.pkl'
cv_filename = 'cv.pkl'

try:
    with open(model_filename, 'rb') as model_file:
        loaded_model = pickle.load(model_file)
except FileNotFoundError:
    raise HTTPException(status_code=500, detail="Model file not found")

try:
    with open(cv_filename, 'rb') as cv_file:
        loaded_cv = pickle.load(cv_file)
except FileNotFoundError:
    raise HTTPException(status_code=500, detail="CountVectorizer file not found")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the index.html file."""
    with open("templates/index.html", "r") as file:
        return file.read()


@app.post("/predict_sentiment")
async def predict_sentiment(review: str = Form(...)):
    """Predict the sentiment of the provided review."""
    try:
        # Preprocess the input text
        text = review
        text = re.sub('[^a-zA-Z]', ' ', text).lower().split()
        ps = PorterStemmer()
        stop_words = stopwords.words('indonesian')
        text = ' '.join(ps.stem(word) for word in text if word not in stop_words)

        # Transform the text using the loaded CountVectorizer
        X_new = loaded_cv.transform([text]).toarray()

        # Make the prediction
        prediction = loaded_model.predict(X_new)[0]

        # Map prediction to sentiment
        sentiment_mapping = {1: "Negative", 2: "Neutral", 3: "Positive"}
        sentiment = sentiment_mapping.get(prediction, "Unknown")

        return {"sentiment": sentiment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during prediction: {e}")
