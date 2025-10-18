# app.py - Fixed Emotion Detection
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import os
import re

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
        # Enhanced emotion keywords with more patterns
        self.emotions = {
            'sad': [
                'sad', 'depressed', 'unhappy', 'down', 'crying', 'hopeless', 'miserable',
                'heartbroken', 'tears', 'grief', 'sorrow', 'disappointed', 'hurt',
                'devastated', 'broken', 'blue', 'gloomy', 'despair', 'upset'
            ],
            'anxious': [
                'anxious', 'worried', 'nervous', 'scared', 'panic', 'stress', 'afraid',
                'fear', 'terrified', 'overwhelmed', 'tense', 'uneasy', 'paranoid',
                'restless', 'edgy', 'jittery', 'worried', 'concern', 'dread'
            ],
            'angry': [
                'angry', 'mad', 'furious', 'frustrated', 'irritated', 'annoyed', 'rage',
                'hate', 'pissed', 'enraged', 'livid', 'outraged', 'resentful',
                'bitter', 'hostile', 'aggravated', 'infuriated'
            ],
            'stressed': [
                'stressed', 'overwhelmed', 'pressure', 'burnout', 'exhausted', 'tired',
                'overworked', 'burden', 'swamped', 'loaded', 'drained', 'stretched',
                'struggling', 'cant cope', 'too much'
            ],
            'lonely': [
                'lonely', 'alone', 'isolated', 'empty', 'abandoned', 'rejected',
                'unwanted', 'friendless', 'solitary', 'disconnected', 'excluded',
                'forgotten', 'left out', 'nobody cares'
            ],
            'happy': [
                'happy', 'great', 'wonderful', 'excited', 'joyful', 'amazing', 'fantastic',
                'awesome', 'excellent', 'good', 'blessed', 'grateful', 'love', 'best',
                'perfect', 'delighted', 'thrilled', 'cheerful', 'pleased'
            ]
        }
        
        # Contextual phrases that indicate emotions
        self.emotion_phrases = {
            'sad': [
                'want to cry', 'feel like crying', 'cant stop crying', 'feel empty',
                'nothing matters', 'gave up', 'no point', 'feel worthless'
            ],
            'anxious': [
                'cant sleep', 'heart racing', 'cant breathe', 'panic attack',
                'constantly worrying', 'what if', 'scared that', 'afraid of'
            ],
            'angry': [
                'so angry', 'makes me mad', 'cant stand', 'hate when', 'fed up',
                'had enough', 'pisses me off', 'driving me crazy'
            ],
            'stressed': [
                'too much work', 'cant handle', 'breaking point', 'about to crack',
                'drowning in', 'buried in work', 'no time', 'everything at once'
            ],
            'lonely': [
                'no one to talk', 'have no friends', 'all alone', 'nobody understands',
                'feel invisible', 'no one cares', 'by myself'
            ]
        }
        
        self.solutions = {
            'sad': [
                "🌟 Try the 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, and 1 you taste",
                "💙 Reach out to someone you trust - a friend, family member, or therapist. Talking helps more than we realize",
                "☀️ Get some natural sunlight or take a 10-minute walk outside. Movement and light can shift your mood",
                "🏃 Do 10-15 minutes of physical activity - even gentle stretching or dancing can release endorphins",
                "📝 Write down three things you're grateful for today, even small things like a warm cup of tea"
            ],
            'anxious': [
                "🫁 Deep breathing exercise: Inhale for 4 counts, hold for 4, exhale for 6. Repeat 5 times",
                "🧊 Hold an ice cube in your hand to ground yourself in the present moment",
                "🎯 Focus on what you CAN control right now. Let go of 'what ifs' for the next 10 minutes",
                "✍️ Journal your worries: write them all down, then close the notebook. They're stored safely",
                "🧘 Try a 5-minute guided meditation (YouTube has many free ones for anxiety)"
            ],
            'angry': [
                "⏸️ Take a 10-minute timeout. Step away from the situation physically if possible",
                "🥊 Physical release: go for a brisk walk, do jumping jacks, or punch a pillow safely",
                "🔢 Count backwards from 20 slowly, taking deep breaths between each number",
                "📝 Write an angry letter expressing everything you feel (don't send it). Then tear it up or delete it",
                "🗣️ Use 'I feel' statements when ready to talk: 'I feel frustrated when...' instead of 'You always...'"
            ],
            'stressed': [
                "⏰ Try the Pomodoro technique: Work for 25 minutes, then take a 5-minute break",
                "📋 Make a priority list: pick ONE task to focus on right now. Just one",
                "🛁 Practice immediate self-care: take a warm bath, eat a good meal, or rest for 20 minutes",
                "🚫 Practice saying 'no' to non-essential commitments this week",
                "😄 Schedule 30 minutes of fun today - watch a show, play a game, call a friend"
            ],
            'lonely': [
                "📞 Call or text someone you haven't talked to in a while. Just say 'hi, thinking of you'",
                "🌐 Join online communities around your interests (Reddit, Discord, Facebook groups)",
                "🤝 Look into volunteering - helping others creates genuine connections",
                "☕ Visit a café or public space - sometimes just being around people helps",
                "🎭 Join a class, club, or group activity (book clubs, sports, art classes, etc.)"
            ]
        }
    
    def detect_emotion(self, text):
        text_lower = text.lower()
        
        # Score emotions based on keywords
        emotion_scores = {emotion: 0 for emotion in self.emotions.keys()}
        
        # Check for individual keywords
        for emotion, keywords in self.emotions.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    emotion_scores[emotion] += 2  # Weight individual keywords
        
        # Check for contextual phrases (higher weight)
        for emotion, phrases in self.emotion_phrases.items():
            for phrase in phrases:
                if phrase in text_lower:
                    emotion_scores[emotion] += 5  # Phrases get more weight
        
        # Find the dominant emotion
        max_score = max(emotion_scores.values())
        
        if max_score > 0:
            emotion = max(emotion_scores, key=emotion_scores.get)
            intensity = min(max_score / 10, 1.0)  # Normalize intensity
        else:
            # Default to neutral/happy for positive or unclear messages
            emotion = 'neutral'
            intensity = 0.3
        
        # Calculate sentiment score (simple version)
        positive_words = ['good', 'great', 'happy', 'love', 'wonderful', 'amazing', 'best', 'excellent']
        negative_words = ['bad', 'sad', 'hate', 'terrible', 'awful', 'worst', 'horrible', 'pain']
        
        sentiment = 0
        for word in positive_words:
            if word in text_lower:
                sentiment += 0.2
        for word in negative_words:
            if word in text_lower:
                sentiment -= 0.2
        
        sentiment = max(-1, min(1, sentiment))  # Clamp between -1 and 1
        
        return {
            'emotion': emotion,
            'intensity': round(intensity, 2),
            'sentiment_score': round(sentiment, 2)
        }
    
    def create_response(self, emotion, intensity, user_name, user_message):
        # If emotion is detected and negative
        if emotion in ['sad', 'anxious', 'angry', 'stressed', 'lonely']:
            opening = f"I hear you, {user_name}. It sounds like you're feeling {emotion}. Those feelings are completely valid."
            
            # Get 3 random solutions for this emotion
            solutions = random.sample(
                self.solutions.get(emotion, []), 
                min(3, len(self.solutions.get(emotion, [])))
            )
            
            sol_text = "\n\n**Here are some strategies that might help:**\n\n"
            sol_text += "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(solutions))
            
            # Add crisis resources for high intensity
            if intensity > 0.7 or any(word in user_message.lower() for word in ['suicide', 'kill myself', 'end it all', 'want to die']):
                sol_text += "\n\n🆘 **If you're in crisis, please reach out immediately:**\n"
                sol_text += "• Call/Text **988** (US Suicide & Crisis Lifeline)\n"
                sol_text += "• Text **HOME** to **741741** (Crisis Text Line)\n"
                sol_text += "• Visit your nearest emergency room\n"
                sol_text += "• Call **911** if in immediate danger"
            
            return f"{opening}{sol_text}\n\n💬 I'm here to listen. Would you like to talk more about what's going on?"
        
        elif emotion == 'happy':
            return f"That's wonderful, {user_name}! 😊 I'm so glad you're feeling happy! Tell me more about what's making you feel this way. Celebrating the good moments is important!"
        
        else:
            # Neutral or unclear emotion
            return f"Thanks for sharing, {user_name}. I'm here to listen and support you. Could you tell me a bit more about how you're feeling right now? Are you doing okay?"

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
            flex-shrink: 0;
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
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
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
            font-size: 15px;
        }
        .hidden { display: none !important; }
        .typing {
            display: inline-block;
            padding: 10px 15px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .typing span {
            height: 10px;
            width: 10px;
            background: #667eea;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing span:nth-child(1) { animation-delay: -0.32s; }
        .typing span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="modal" id="modal">
        <div class="modal-content">
            <h2>🤗 Welcome to Emotional Buddy</h2>
            <p>What should I call you?</p>
            <input type="text" id="nameInput" placeholder="Enter your name" maxlength="50">
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
                <div class="content">Hi! I'm here to listen and support you. Share how you're feeling, and I'll do my best to help 💙</div>
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
        let isProcessing = false;
        
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
            document.getElementById('userInput').focus();
            addBot(`Welcome ${userName}! How are you feeling today? You can share anything with me.`);
        }
        
        async function send() {
            if (isProcessing) return;
            
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            isProcessing = true;
            document.getElementById('sendBtn').disabled = true;
            
            addUser(msg);
            input.value = '';
            
            // Show typing indicator
            const typingId = showTyping();
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: userId, message: msg, user_name: userName})
                });
                const data = await res.json();
                
                // Remove typing indicator
                removeTyping(typingId);
                
                if (data.success) {
                    addBot(data.response);
                } else {
                    addBot("I'm sorry, I'm having trouble right now. Please try again.");
                }
            } catch (error) {
                removeTyping(typingId);
                addBot("I'm sorry, something went wrong. Please try again.");
            }
            
            isProcessing = false;
            document.getElementById('sendBtn').disabled = false;
            input.focus();
        }
        
        function showTyping() {
            const div = document.createElement('div');
            div.className = 'message bot';
            div.id = 'typing-' + Date.now();
            div.innerHTML = `
                <div class="avatar">🤗</div>
                <div class="typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
            document.getElementById('messages').appendChild(div);
            scroll();
            return div.id;
        }
        
        function removeTyping(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
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
            if (e.key === 'Enter' && !isProcessing) send();
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
        
        # Detect emotion from message
        analysis = engine.detect_emotion(message)
        
        # Create personalized response
        response = engine.create_response(
            analysis['emotion'],
            analysis['intensity'],
            user_name,
            message
        )
        
        # Save to database
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
        return jsonify({'success': False, 'error': str(e), 'response': 'I apologize, but I encountered an error. Please try again.'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
