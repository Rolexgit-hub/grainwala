import pickle, json, random, re

# Load ML files
model = pickle.load(open("model/chatbot_model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

# Load intents
with open("intents.json", encoding="utf-8") as f:
    intents = json.load(f)

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s\u0900-\u097F]", "", text)
    return text

def detect_lang(text):
    return "hi" if re.search(r"[\u0900-\u097F]", text) else "en"

def get_response(msg):
    msg_clean = clean_text(msg)
    X = vectorizer.transform([msg_clean])
    tag_id = model.predict(X)[0]
    tag = le.inverse_transform([tag_id])[0]
    lang = detect_lang(msg)

    for intent in intents["intents"]:
        if intent["tag"] == tag:
            responses = intent["responses_hi"] if lang == "hi" else intent["responses_en"]
            return random.choice(responses)

    return "मुझे समझ नहीं आया। कृपया फिर से पूछिए।"
