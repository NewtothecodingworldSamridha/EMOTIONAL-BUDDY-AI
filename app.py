from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import random
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'emotional-buddy-secret-2024')
CORS(app)

conversations = []
users = {}
user_counter = 0

class AdvancedEmotionEngine:
    def __init__(self):
        # Expanded keywords with more variations
        self.emotion_keywords = {
            'sad': {
                'words': ['sad', 'depressed', 'unhappy', 'down', 'crying', 'cry', 'cried', 'hopeless', 'miserable', 
                         'heartbroken', 'tears', 'upset', 'hurt', 'hurting', 'pain', 'painful', 'broken', 'devastated',
                         'disappointed', 'disappointing', 'blue', 'gloomy', 'despair', 'grief', 'sorrow', 'tragic',
                         'awful', 'terrible', 'worst', 'horrible'],
                'phrases': ['want to cry', 'feel like crying', 'cant stop crying', 'feel empty', 'feel bad',
                           'feel terrible', 'feel awful', 'nothing matters', 'gave up', 'give up', 'no point',
                           'feel worthless', 'dont want to', 'cant take it', 'breaking down', 'falling apart']
            },
            'anxious': {
                'words': ['anxious', 'anxiety', 'worried', 'worry', 'worrying', 'nervous', 'scared', 'afraid',
                         'panic', 'panicking', 'panicked', 'stress', 'stressed', 'stressing', 'fear', 'fearful',
                         'terrified', 'overwhelmed', 'overwhelming', 'tense', 'tension', 'uneasy', 'restless',
                         'paranoid', 'concerned', 'dread', 'dreading'],
                'phrases': ['cant sleep', 'cant breathe', 'heart racing', 'racing heart', 'panic attack',
                           'constantly worrying', 'keep worrying', 'what if', 'worried about', 'scared that',
                           'afraid of', 'freaking out', 'nervous about', 'so much stress', 'too much pressure']
            },
            'angry': {
                'words': ['angry', 'anger', 'mad', 'furious', 'frustrated', 'frustrating', 'irritated', 'irritating',
                         'annoyed', 'annoying', 'rage', 'raging', 'hate', 'hating', 'hated', 'pissed', 'enraged',
                         'livid', 'outraged', 'resentful', 'bitter', 'hostile', 'aggravated', 'infuriated'],
                'phrases': ['so angry', 'really angry', 'makes me mad', 'making me mad', 'cant stand', 'hate when',
                           'fed up', 'had enough', 'pisses me off', 'pissing me off', 'driving me crazy',
                           'makes me furious', 'want to scream', 'why would', 'how could', 'cant believe']
            },
            'stressed': {
                'words': ['stressed', 'stress', 'stressful', 'overwhelmed', 'overwhelming', 'pressure', 'pressured',
                         'burnout', 'burnt out', 'exhausted', 'exhausting', 'tired', 'tiring', 'overworked',
                         'burden', 'burdened', 'swamped', 'loaded', 'drained', 'draining', 'stretched', 'struggling'],
                'phrases': ['too much work', 'so much work', 'cant handle', 'cant cope', 'breaking point',
                           'about to crack', 'drowning in', 'buried in', 'no time', 'everything at once',
                           'too many things', 'cant keep up', 'falling behind', 'so much to do']
            },
            'lonely': {
                'words': ['lonely', 'loneliness', 'alone', 'isolated', 'isolating', 'empty', 'emptiness',
                         'abandoned', 'rejected', 'unwanted', 'friendless', 'solitary', 'disconnected',
                         'excluded', 'forgotten', 'invisible', 'misunderstood'],
                'phrases': ['no one to talk', 'no one to talk to', 'have no friends', 'dont have friends',
                           'all alone', 'by myself', 'nobody understands', 'no one understands', 'feel invisible',
                           'no one cares', 'nobody cares', 'left out', 'feel excluded', 'have nobody']
            },
            'happy': {
                'words': ['happy', 'happiness', 'great', 'wonderful', 'excited', 'exciting', 'joyful', 'joy',
                         'amazing', 'fantastic', 'awesome', 'excellent', 'good', 'better', 'best', 'blessed',
                         'grateful', 'thankful', 'love', 'loving', 'perfect', 'delighted', 'thrilled',
                         'cheerful', 'pleased', 'satisfied', 'content', 'proud'],
                'phrases': ['feel great', 'feeling great', 'so happy', 'really happy', 'feel amazing',
                           'going well', 'went well', 'turned out great', 'really good', 'so good',
                           'best day', 'had fun', 'having fun', 'feel blessed', 'feel grateful']
            }
        }
        
        # Negation words to handle "not sad", "not worried" etc
        self.negations = ['not', 'never', 'no', 'dont', 'doesnt', 'didnt', 'wont', 'wouldnt', 'cant', 'cannot']
        
        self.solutions = {
            'sad': [
                "Try the 5-4-3-2-1 grounding technique: Name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste",
                "Reach out to someone you trust - talking helps more than you think",
                "Get some natural light or take a 10-15 minute walk outside",
                "Write down three things you are grateful for today, even small things",
                "Listen to music that matches your mood, then gradually shift to uplifting songs",
                "Do a simple physical activity - even 5 minutes of stretching helps",
                "Allow yourself to feel the emotion without judgment - its okay to be sad"
            ],
            'anxious': [
                "Deep breathing: Inhale for 4 counts, hold for 4, exhale for 6. Repeat 5 times",
                "Hold an ice cube in your hand to ground yourself in the present moment",
                "Focus on what you CAN control right now, let go of what you cannot",
                "Journal your worries - write them all down to get them out of your head",
                "Try the 54321 technique: Name 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste",
                "Challenge your worried thoughts: What evidence do I have? Is this thought helpful?",
                "Progressive muscle relaxation: Tense and release each muscle group for 5 seconds"
            ],
            'angry': [
                "Take a 10-minute timeout before responding to the situation",
                "Physical release: Go for a brisk walk, do jumping jacks, or punch a pillow safely",
                "Count backwards from 20 slowly, taking deep breaths between each number",
                "Write an angry letter expressing everything you feel, then tear it up or delete it",
                "Use I feel statements when ready to talk: I feel frustrated when... instead of You always...",
                "Channel the energy into something productive: cleaning, organizing, exercising",
                "Ask yourself: Will this matter in 5 years? Helps gain perspective"
            ],
            'stressed': [
                "Try the Pomodoro technique: Work for 25 minutes, then take a 5-minute break",
                "Make a priority list and pick ONE task to focus on right now. Just one",
                "Practice immediate self-care: Take a warm bath, eat a good meal, or rest for 20 minutes",
                "Say no to non-essential commitments today or this week",
                "Schedule 30 minutes of fun or relaxation today - its not optional, its necessary",
                "Break big tasks into tiny steps. Focus only on the next small action",
                "Talk to someone about what is stressing you - sharing the load helps"
            ],
            'lonely': [
                "Call or text someone you have not talked to in a while. Just say hi, thinking of you",
                "Join online communities around your interests on Reddit, Discord, or Facebook groups",
                "Look into volunteering opportunities - helping others creates genuine connections",
                "Visit a cafe, library, or public space - sometimes just being around people helps",
                "Join a class, club, or group activity: book clubs, sports teams, art classes, gaming groups",
                "Reach out to an old friend or acquaintance. People are often glad to reconnect",
                "Consider adopting a pet or volunteering at an animal shelter if you love animals"
            ]
        }
    
    def detect_emotion(self, text):
        text_lower = text.lower()
        
        # Remove punctuation for better matching
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        
        # Check for negations nearby emotion words
        words = text_clean.split()
        
        emotion_scores = {emotion: 0 for emotion in self.emotion_keywords.keys()}
        
        # Score based on individual words
        for emotion, data in self.emotion_keywords.items():
            for keyword in data['words']:
                # Find positions of keyword in text
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = list(re.finditer(pattern, text_lower))
                
                for match in matches:
                    # Check if there's a negation word before this keyword
                    start_pos = max(0, match.start() - 20)  # Look 20 chars back
                    context = text_lower[start_pos:match.start()].split()
                    
                    # If negation found nearby, skip this keyword
                    if any(neg in context[-3:] for neg in self.negations):
                        continue
                    
                    emotion_scores[emotion] += 2
        
        # Score based on phrases (higher weight)
        for emotion, data in self.emotion_keywords.items():
            for phrase in data['phrases']:
                if phrase in text_lower:
                    emotion_scores[emotion] += 5
        
        # Additional contextual clues
        # Questions often indicate worry/anxiety
        if '?' in text and any(word in text_lower for word in ['what', 'how', 'why', 'should', 'can']):
            emotion_scores['anxious'] += 1
        
        # Exclamation marks can indicate strong emotion
        exclamation_count = text.count('!')
        if exclamation_count > 0:
            if emotion_scores['angry'] > 0:
                emotion_scores['angry'] += exclamation_count
            if emotion_scores['happy'] > 0:
                emotion_scores['happy'] += exclamation_count
        
        # ALL CAPS indicates strong emotion
        caps_words = [w for w in text.split() if w.isupper() and len(w) > 2]
        if len(caps_words) > 1:
            max_emotion = max(emotion_scores, key=emotion_scores.get)
            if emotion_scores[max_emotion] > 0:
                emotion_scores[max_emotion] += 2
        
        # Find the dominant emotion
        max_score = max(emotion_scores.values())
        
        if max_score > 0:
            emotion = max(emotion_scores, key=emotion_scores.get)
            intensity = min(max_score / 10.0, 1.0)
        else:
            # No clear emotion detected - default to neutral
            emotion = 'neutral'
            intensity = 0.3
        
        return {
            'emotion': emotion,
            'intensity': round(intensity, 2),
            'scores': emotion_scores  # For debugging
        }
    
    def create_response(self, emotion, intensity, user_name):
        if emotion in ['sad', 'anxious', 'angry', 'stressed', 'lonely']:
            # Empathetic opening
            openings = {
                'sad': f"I hear you, {user_name}. Sadness is a heavy feeling, and what you are experiencing is valid.",
                'anxious': f"I understand, {user_name}. Anxiety can feel overwhelming, but you are not alone in this.",
                'angry': f"I hear your frustration, {user_name}. Anger is a natural emotion, and its okay to feel it.",
                'stressed': f"That sounds really stressful, {user_name}. You are carrying a lot right now.",
                'lonely': f"I am sorry you are feeling lonely, {user_name}. Those feelings are real and important."
            }
            
            opening = openings[emotion]
            
            # Select solutions
            solutions_list = self.solutions.get(emotion, [])
            num_solutions = 4 if intensity > 0.5 else 3
            selected = random.sample(solutions_list, min(num_solutions, len(solutions_list)))
            
            sol_text = "\n\nHere are some strategies that might help:\n\n"
            sol_text += "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(selected))
            
            # Crisis resources for high intensity or crisis keywords
            crisis_keywords = ['suicide', 'kill myself', 'end it all', 'want to die', 'better off dead', 'no reason to live']
            is_crisis = intensity > 0.8 or any(kw in user_name.lower() for kw in crisis_keywords)
            
            if is_crisis:
                sol_text += "\n\n🆘 CRISIS RESOURCES - Please reach out:\n"
                sol_text += "• Call or Text 988 (US Suicide & Crisis Lifeline)\n"
                sol_text += "• Text HOME to 741741 (Crisis Text Line)\n"
                sol_text += "• Call 911 if in immediate danger\n"
                sol_text += "• Go to your nearest emergency room"
            
            return f"{opening}{sol_text}\n\nI am here for you. Want to talk more about what you are going through?"
        
        elif emotion == 'happy':
            responses = [
                f"That is wonderful, {user_name}! I am so glad you are feeling good! What is making you happy today?",
                f"I love hearing that, {user_name}! Your happiness is important. Tell me more about what is going well!",
                f"That is fantastic, {user_name}! It is great to celebrate the good moments. What happened?"
            ]
            return random.choice(responses)
        
        else:
            # Neutral - ask for clarification
            return f"Thanks for sharing, {user_name}. I am here to listen and support you. Could you tell me a bit more about how you are feeling right now?"

engine = AdvancedEmotionEngine()

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emotional Buddy AI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
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
            padding: 20px;
            border-radius: 20px 20px 0 0;
            text-align: center;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin: 15px 0;
            display: flex;
            gap: 10px;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
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
            flex-shrink: 0;
        }
        .content {
            max-width: 70%;
            padding: 15px;
            border-radius: 15px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        .message.bot .content {
            background: white;
            color: #333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .message.user .content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
            display: flex;
            gap: 10px;
        }
        #userInput {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 20px;
            font-size: 15px;
            outline: none;
        }
        #userInput:focus { border-color: #667eea; }
        button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { transform: translateY(-2px); transition: 0.2s; }
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 400px;
        }
        .modal-content h2 { color: #667eea; margin-bottom: 20px; }
        .modal-content input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 15px;
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="modal" id="modal">
        <div class="modal-content">
            <h2>🤗 Welcome</h2>
            <p>What is your name?</p>
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
                <div class="content">Hi! I am here to listen and support you. Share how you are feeling - I understand a wide range of emotions and I am here to help.</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Type anything you are feeling..." disabled>
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
                addBot('Welcome ' + userName + '! How are you feeling today? You can share anything with me.');
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
                addBot("I am here to help. Please try again.");
            });
        }
        
        function addUser(text) {
            const div = document.createElement('div');
            div.className = 'message user';
            div.innerHTML = '<div class="content">' + escapeHtml(text) + '</div><div class="avatar">👤</div>';
            document.getElementById('messages').appendChild(div);
            scroll();
        }
        
        function addBot(text) {
            const div = document.createElement('div');
            div.className = 'message bot';
            div.innerHTML = '<div class="avatar">🤗</div><div class="content">' + escapeHtml(text) + '</div>';
            document.getElementById('messages').appendChild(div);
            scroll();
        }
        
        function scroll() {
            const m = document.getElementById('messages');
            m.scrollTop = m.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        document.getElementById('userInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') send();
        });
        
        document.getElementById('nameInput').addEventListener('keypress', function(e) {
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
        response = engine.create_response(analysis['emotion'], analysis['intensity'], user_name)
        
        conversations.append({
            'user_id': user_id,
            'message': message,
            'response': response,
            'emotion': analysis['emotion'],
            'intensity': analysis['intensity']
        })
        
        return jsonify({
            'success': True,
            'response': response,
            'emotion': analysis['emotion'],
            'intensity': analysis['intensity']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'response': 'I am here to help. Could you tell me more?',
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
