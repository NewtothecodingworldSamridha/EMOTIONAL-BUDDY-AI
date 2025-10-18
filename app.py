# app.py - Complete Flask Application
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import json
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

Base = declarative_base()
engine = create_engine('sqlite:///emotional_buddy.db', echo=False)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    mood_score = Column(Float, default=0.0)

class Conversation(Base):
    __tablename__ = 'conversations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    emotion_detected = Column(String(50))
    sentiment_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

class EmotionEngine:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.emotions = {
            'sad': ['sad', 'depressed', 'unhappy', 'down', 'crying', 'hopeless'],
            'anxious': ['anxious', 'worried', 'nervous', 'scared', 'panic', 'stress'],
            'angry': ['angry', 'mad', 'furious', 'frustrated', 'irritated'],
            'stressed': ['stressed', 'overwhelmed', 'pressure', 'burnout'],
            'lonely': ['lonely', 'alone', 'isolated', 'empty'],
            'happy': ['happy', 'great', 'wonderful', 'excited', 'joyful']
        }
        
        self.solutions = {
            'sad': [
                "🌟 Try 5-4-3-2-1 grounding: Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste",
                "💙 Reach out to someone you trust - talking helps",
                "☀️ Get some natural light or take a short walk",
                "🏃 Do 10 minutes of physical activity",
                "📝 Write down three things you're grateful for"
            ],
            'anxious': [
                "🫁 Deep breathing: Inhale 4 counts, hold 4, exhale 6",
                "🧊 Hold ice to ground yourself in the present",
                "🎯 Focus on what you CAN control right now",
                "✍️ Journal your worries to process them",
                "🧘 Try 5 minutes of meditation"
            ],
            'angry': [
                "⏸️ Take a 10-minute timeout",
                "🥊 Physical release: walk, exercise, or punch a pillow",
                "🔢 Count backwards from 10 slowly",
                "📝 Write an angry letter (don't send) then tear it up",
                "🗣️ Use 'I feel' statements instead of blame"
            ],
            'stressed': [
                "⏰ Try Pomodoro: 25min work, 5min break",
                "📋 Make a priority list - one task at a time",
                "🛁 Practice self-care: bath, good meal, rest",
                "🚫 Say no to non-essential commitments",
                "😄 Schedule fun activities weekly"
            ],
            'lonely': [
                "📞 Call or text someone",
                "🌐 Join online communities around your interests",
                "🤝 Volunteer - helping creates connections",
                "☕ Go to a café - being around people helps",
                "🎭 Join classes or clubs"
            ]
        }
    
    def detect_emotion(self, text):
        text_lower = text.lower()
        scores = {}
        for emotion, keywords in self.emotions.items():
            scores[emotion] = sum(1 for kw in keywords if kw in text_lower)
        
        max_score = max(scores.values())
        if max_score > 0:
            emotion = max(scores, key=scores.get)
            intensity = min(max_score / 3, 1.0)
        else:
            emotion = 'neutral'
            intensity = 0.3
        
        sentiment = self.vader.polarity_scores(text)['compound']
        
        return {
            'emotion': emotion,
            'intensity': round(intensity, 2),
            'sentiment_score': round(sentiment, 2)
        }
    
    def create_response(self, emotion, intensity, user_name):
        if emotion in ['sad', 'anxious', 'angry', 'stressed', 'lonely']:
            opening = f"I hear you, {user_name}. {emotion.capitalize()} feelings are valid and important."
            solutions = random.sample(self.solutions.get(emotion, []), min(3, len(self.solutions.get(emotion, []))))
            sol_text = "\n\n**Here are some strategies:**\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(solutions))
            
            if intensity > 0.7:
                sol_text += "\n\n🆘 If you're in crisis:\n• Call 988 (US Suicide Prevention)\n• Text HOME to 741741"
            
            return f"{opening}{sol_text}\n\n💬 Want to talk more about this?"
        else:
            return f"That's wonderful, {user_name}! Tell me more about what's making you feel this way!"

engine = EmotionEngine()

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emotional Buddy AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 800px;
            height: 85vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 24px 24px 0 0;
            text-align: center;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f9fafb;
        }
        .message {
            margin: 15px 0;
            display: flex;
            gap: 10px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { flex-direction: row-reverse; }
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .content {
            max-width: 70%;
            padding: 15px 20px;
            border-radius: 20px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .message.bot .content {
            background: white;
            color: #1f2937;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .message.user .content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 10px;
        }
        #userInput {
            flex: 1;
            padding: 12px 20px;
            border: 2px solid #e5e7eb;
            border-radius: 24px;
            font-size: 15px;
            outline: none;
        }
        #userInput:focus { border-color: #667eea; }
        button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            font-weight: 600;
        }
        button:hover { transform: translateY(-2px); }
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 40px;
            border-radius: 24px;
            text-align: center;
            max-width: 400px;
        }
        .modal-content h2 { color: #667eea; margin-bottom: 20px; }
        .modal-content input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="modal" id="modal">
        <div class="modal-content">
            <h2>🤗 Welcome!</h2>
            <p>What's your name?</p>
            <input type="text" id="nameInput" placeholder="Enter your name">
            <button onclick="start()">Start Chat</button>
        </div>
    </div>
    <div class="container">
        <div class="header">
            <h1>🤗 Emotional Buddy AI</h1>
            <p>Your compassionate mental health companion</p>
        </div>
        <div class="messages" id="messages">
            <div class="message bot">
                <div class="avatar">🤗</div>
                <div class="content">Hi! I'm here to listen and support you. Share how you're feeling 💙</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Share your feelings..." disabled>
            <button onclick="send()" id="sendBtn" disabled>Send</button>
        </div>
    </div>
    <script>
        let userId = null;
        let userName = 'Friend';
        
        async function start() {
            userName = document.getElementById('nameInput').value.trim() || 'Friend';
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: userName})
            });
            const data = await res.json();
            userId = data.user_id;
            document.getElementById('modal').classList.add('hidden');
            document.getElementById('userInput').disabled = false;
            document.getElementById('sendBtn').disabled = false;
            addBot(`Welcome ${userName}! How are you feeling today?`);
        }
        
        async function send() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            addUser(msg);
            input.value = '';
            
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId, message: msg, user_name: userName})
            });
            const data = await res.json();
            addBot(data.response);
        }
        
        function addUser(text) {
            const div = document.createElement('div');
            div.className = 'message user';
            div.innerHTML = `<div class="content">${esc(text)}</div><div class="avatar">👤</div>`;
            document.getElementById('messages').appendChild(div);
            scroll();
        }
        
        function addBot(text) {
            const div = document.createElement('div');
            div.className = 'message bot';
            div.innerHTML = `<div class="avatar">🤗</div><div class="content">${esc(text)}</div>`;
            document.getElementById('messages').appendChild(div);
            scroll();
        }
        
        function scroll() {
            const m = document.getElementById('messages');
            m.scrollTop = m.scrollHeight;
        }
        
        function esc(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        document.getElementById('userInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') send();
        });
        
        document.getElementById('nameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') start();
        });
    </script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        session = Session()
        user = User(name=data.get('name', 'Friend'))
        session.add(user)
        session.commit()
        user_id = user.id
        session.close()
        return jsonify({'success': True, 'user_id': user_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get('user_id', 0)
        message = data.get('message', '')
        user_name = data.get('user_name', 'Friend')
        
        analysis = engine.detect_emotion(message)
        response = engine.create_response(
            analysis['emotion'],
            analysis['intensity'],
            user_name
        )
        
        session = Session()
        conv = Conversation(
            user_id=user_id,
            message=message,
            response=response,
            emotion_detected=analysis['emotion'],
            sentiment_score=analysis['sentiment_score']
        )
        session.add(conv)
        session.commit()
        session.close()
        
        return jsonify({
            'success': True,
            'response': response,
            'emotion_analysis': analysis
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
