# app.py - Stable Version with Working Emotion Detection
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from datetime import datetime
import random
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
CORS(app)

# Simple in-memory storage (no database issues)
conversations = []
users = {}
user_counter = 0

class EmotionEngine:
    def __init__(self):
        self.emotions = {
            'sad': ['sad', 'depressed', 'unhappy', 'down', 'crying', 'cry', 'hopeless', 
                    'miserable', 'heartbroken', 'tears', 'upset', 'hurt', 'pain', 'broken'],
            'anxious': ['anxious', 'worried', 'nervous', 'scared', 'panic', 'stress', 
                        'afraid', 'fear', 'terrified', 'overwhelmed', 'worry', 'tension'],
            'angry': ['angry', 'mad', 'furious', 'frustrated', 'irritated', 'annoyed', 
                      'rage', 'hate', 'pissed', 'enraged', 'livid'],
            'stressed': ['stressed', 'overwhelmed', 'pressure', 'burnout', 'exhausted', 
                         'tired', 'overworked', 'burden', 'swamped', 'drained'],
            'lonely': ['lonely', 'alone', 'isolated', 'empty', 'abandoned', 'rejected', 
                       'friendless', 'solitary', 'disconnected'],
            'happy': ['happy', 'great', 'wonderful', 'excited', 'joyful', 'amazing', 
                      'fantastic', 'awesome', 'excellent', 'good', 'blessed', 'love', 'best']
        }
        
        self.solutions = {
            'sad': [
                "🌟 Try the 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste",
                "💙 Reach out to someone you trust - talking helps more than you think",
                "☀️ Get some natural light or take a 10-minute walk outside",
                "📝 Write down three things you're grateful for today"
            ],
            'anxious': [
                "🫁 Deep breathing: Inhale for 4 counts, hold for 4, exhale for 6. Repeat 5 times",
                "🧊 Hold an ice cube to ground yourself in the present moment",
                "🎯 Focus on what you CAN control right now",
                "✍️ Journal your worries to process them"
            ],
            'angry': [
                "⏸️ Take a 10-minute timeout before responding",
                "🥊 Physical release: walk, exercise, or punch a pillow",
                "🔢 Count backwards from 20 slowly",
                "🗣️ Use 'I feel' statements instead of blame"
            ],
            'stressed': [
                "⏰ Try Pomodoro: 25min work, 5min break",
                "📋 Make a priority list - one task at a time",
                "🛁 Practice self-care: bath, meal, or rest",
                "🚫 Say no to non-essential things today"
            ],
            'lonely': [
                "📞 Call or text someone you care about",
                "🌐 Join online communities around your interests",
                "🤝 Consider volunteering - it creates connections",
                "☕ Visit a café - being around people helps"
            ]
        }
    
    def detect_emotion(self, text):
        text_lower = text.lower()
        scores = {}
        
        for emotion, keywords in self.emotions.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            scores[emotion] = score
        
        max_score = max(scores.values())
        
        if max_score > 0:
            emotion = max(scores, key=scores.get)
            intensity = min(max_score / 5.0, 1.0)
        else:
            emotion = 'neutral'
            intensity = 0.3
        
        return {
            'emotion': emotion,
            'intensity': round(intensity, 2)
        }
    
    def create_response(self, emotion, intensity, user_name):
        if emotion in ['sad', 'anxious', 'angry', 'stressed', 'lonely']:
            opening = f"I hear you, {user_name}. Feeling {emotion} is tough, and your feelings are valid."
            
            solutions_list = self.solutions.get(emotion, [])
            selected = random.sample(solutions_list, min(3, len(solutions_list)))
            
            sol_text = "\n\n**Here are some things that might help:**\n\n"
            sol_text += "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(selected))
            
            if intensity > 0.7:
                sol_text += "\n\n🆘 **If you're in crisis:**\n• Call/Text 988 (US)\n• Text HOME to 741741"
            
            return f"{opening}{sol_text}\n\n💬 Want to talk more about it?"
        
        elif emotion == 'happy':
            return f"That's wonderful, {user_name}! 😊 I'm so glad you're feeling good! What's making you happy today?"
        
        else:
            return f"Thanks for sharing, {user_name}. I'm here to listen. How are you feeling right now?"

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
            <input type="text" id="userInput" placeholder="Type your message..." disabled>
            <button onclick="send()" id="sendBtn" disabled>Send</button>
        </div>
    </div>
    <script>
        let userId = null;
        let userName = 'Friend';
        
        function start() {
            userName = document.getElementById('nameInput').value.trim() || 'Friend';
            fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: userName})
            }).then(r => r.json()).then(data => {
                userId = data.user_id;
                document.getElementById('modal').classList.add('hidden');
                document.getElementById('userInput').disabled = false;
                document.getElementById('sendBtn').disabled = false;
                addBot(`Welcome ${userName}! How are you feeling today?`);
            });
        }
        
        function send() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            addUser(msg);
            input.value = '';
            
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId, message: msg, user_name: userName})
            }).then(r => r.json()).then(data => {
                addBot(data.response);
            }).catch(() => {
                addBot("Sorry, something went wrong. Please try again.");
            });
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
    global user_counter
    try:
        data = request.json
        user_counter += 1
        users[user_counter] = {'name': data.get('name', 'Friend')}
        return jsonify({'success': True, 'user_id': user_counter})
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
        
        conversations.append({
            'user_id': user_id,
            'message': message,
            'response': response,
            'emotion': analysis['emotion']
        })
        
        return jsonify({
            'success': True,
            'response': response,
            'emotion': analysis['emotion']
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'response': "I'm here to help. Could you tell me more?",
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

6. Commit with message: `Stable version - removed database`

---

### Step 2: Update `requirements.txt`

1. Click on `requirements.txt`
2. Edit and replace with:
```
flask==3.0.3
flask-cors==4.0.1
gunicorn==22.0.0
