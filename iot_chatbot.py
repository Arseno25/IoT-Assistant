import openai
import os
from dotenv import load_dotenv
import re
import logging
from database import Database
from flask import Flask, request, jsonify, render_template
from datetime import datetime

# Load environment variables
load_dotenv()

# Set the API configuration
openai.api_base = "https://api.netmind.ai/inference-api/openai/v1"
openai.api_key = os.getenv("NETMIND_API_KEY")

app = Flask(__name__)
chatbot = None

class IoTChatbot:
    def __init__(self):
        self.available_models = [
            'meta-llama/Llama-4-Maverick-17B-128E-Instruct',
        ]
        self.db = Database()
        
        self.system_prompt = """You are an advanced IoT and Embedded Systems expert with strong capabilities in data analysis, machine learning, and system optimization. While your primary expertise is in IoT and Embedded Systems, you also have a broad understanding of related technology fields.

Your expertise includes:

1. IoT and Embedded Systems Development:
   - Microcontrollers (ESP32, Arduino, Raspberry Pi, STM32)
   - IoT Protocols (MQTT, CoAP, HTTP, WebSocket, LoRa, Zigbee)
   - Sensor Integration and Data Processing
   - RTOS and Real-time Systems
   - Low-power Design
   - Firmware Development
   - Wireless Communication
   - IoT Security

2. Data Analysis and Processing:
   - Time-series data analysis
   - Sensor data processing and filtering
   - Statistical analysis of IoT data
   - Pattern recognition in sensor readings
   - Anomaly detection
   - Data visualization
   - Predictive maintenance analysis
   - Energy consumption optimization

3. Machine Learning and AI:
   - Edge AI implementation
   - TinyML for microcontrollers
   - Sensor data classification
   - Predictive analytics
   - Anomaly detection models
   - Optimization algorithms
   - Neural networks for embedded systems

4. Related Technology Fields:
   - General Electronics and Circuit Design
   - Programming and Software Development
   - Networking and Communication Systems
   - Cloud Computing and Edge Computing
   - Data Science and Analytics
   - Artificial Intelligence and Machine Learning
   - Cybersecurity and Information Security
   - Industrial Automation and Control Systems
   - Smart Home and Building Automation
   - Robotics and Automation
   - Renewable Energy Systems
   - Environmental Monitoring
   - Healthcare Technology
   - Transportation Systems
   - Agricultural Technology

5. Response Guidelines:
   - Answer questions about IoT and Embedded Systems with full expertise
   - For related technology questions, provide answers while connecting them to IoT where relevant
   - For general technology questions, explain how IoT concepts might apply
   - Provide clear, concise explanations without code unless specifically requested
   - Include code only when specifically requested or when it's essential to the explanation
   - Always explain concepts in simple terms first
   - Use analogies when helpful for understanding
   - Break down complex topics into digestible parts
   - Provide real-world examples when relevant
   - Include best practices and security considerations
   - Consider power consumption and resource constraints
   - Suggest appropriate hardware and software solutions
   - Provide troubleshooting steps for common issues

6. Response Format:
   - Start with a brief overview of the answer
   - Use bullet points or numbered lists for clarity
   - Include diagrams or visual explanations when helpful
   - Add code examples only when necessary
   - End with a summary or next steps
   - Include relevant resources or references
   - For non-IoT topics, explain IoT connections where relevant

7. Important:
   - Maintain primary focus on IoT and Embedded Systems
   - Be friendly and approachable
   - Use clear, professional language
   - Provide practical, actionable advice
   - Consider different skill levels in explanations
   - Encourage follow-up questions
   - Maintain context awareness
   - Suggest related topics when relevant
   - Connect general technology concepts to IoT where possible"""

    def is_greeting(self, message):
        greetings = [
            'hi', 'hello', 'hey', 'hai', 'halo', 'hay', 'hola', 'greetings',
            'good morning', 'good afternoon', 'good evening', 'selamat pagi',
            'selamat siang', 'selamat sore', 'selamat malam'
        ]
        message = message.lower().strip()
        return any(greeting in message for greeting in greetings)

    def get_greeting_response(self):
        responses = [
            "Hello! I'm your IoT and Embedded Systems expert. I can help you with IoT projects, embedded systems, and related technologies. What would you like to know?",
            "Hi there! I'm here to assist you with IoT and embedded systems topics. How can I help you today?",
            "Greetings! I'm your IoT assistant, ready to help with your IoT and embedded systems questions.",
            "Hello! I'm excited to help you with your IoT and embedded systems projects. What would you like to know?",
            "Hi! I'm your IoT expert. I can help you with microcontrollers, sensors, IoT protocols, and more. What's your question?"
        ]
        import random
        return random.choice(responses)

    def analyze_question_type(self, message):
        """Analyze the type of question to determine the appropriate response format"""
        message = message.lower()
        
        # Expanded categories of keywords
        keyword_categories = {
            'iot_core': {
                'hardware': [
                    'microcontroller', 'esp32', 'arduino', 'raspberry pi', 'stm32',
                    'sensor', 'actuator', 'board', 'circuit', 'component', 'hardware',
                    'device', 'module', 'shield', 'breakout', 'pin', 'gpio', 'i2c',
                    'spi', 'uart', 'adc', 'dac', 'pwm', 'relay', 'motor', 'led',
                    'display', 'screen', 'camera', 'rfid', 'nfc', 'bluetooth',
                    'wifi', 'ethernet', 'usb', 'serial', 'power', 'battery'
                ],
                'software': [
                    'firmware', 'code', 'program', 'software', 'library', 'api',
                    'sdk', 'ide', 'compiler', 'debug', 'upload', 'flash', 'bootloader',
                    'os', 'operating system', 'rtos', 'thread', 'task', 'process',
                    'memory', 'storage', 'file', 'database', 'log', 'error'
                ],
                'protocols': [
                    'mqtt', 'coap', 'http', 'websocket', 'lora', 'zigbee', 'bluetooth',
                    'wifi', 'tcp', 'udp', 'ip', 'network', 'protocol', 'communication',
                    'wireless', 'rf', 'radio', 'signal', 'packet', 'frame', 'header',
                    'payload', 'encryption', 'security', 'authentication'
                ],
                'concepts': [
                    'iot', 'internet of things', 'embedded', 'system', 'architecture',
                    'design', 'development', 'implementation', 'deployment', 'testing',
                    'monitoring', 'control', 'automation', 'smart', 'intelligent',
                    'real-time', 'low-power', 'energy', 'efficiency', 'optimization',
                    'performance', 'reliability', 'scalability', 'security', 'privacy',
                    'data', 'analytics', 'processing', 'storage', 'cloud', 'edge',
                    'fog', 'gateway', 'server', 'client', 'node', 'network', 'mesh',
                    'cluster', 'distributed', 'centralized', 'decentralized'
                ]
            },
            'related_tech': {
                'electronics': [
                    'electronics', 'circuit', 'schematic', 'pcb', 'component',
                    'resistor', 'capacitor', 'transistor', 'diode', 'ic',
                    'power supply', 'voltage', 'current', 'resistance',
                    'analog', 'digital', 'signal', 'frequency', 'oscillator'
                ],
                'programming': [
                    'programming', 'coding', 'algorithm', 'data structure',
                    'python', 'c++', 'java', 'javascript', 'rust', 'go',
                    'function', 'class', 'object', 'variable', 'loop',
                    'condition', 'array', 'list', 'string', 'integer'
                ],
                'networking': [
                    'network', 'internet', 'web', 'server', 'client',
                    'protocol', 'tcp/ip', 'dns', 'dhcp', 'firewall',
                    'router', 'switch', 'gateway', 'proxy', 'vpn'
                ],
                'cloud': [
                    'cloud', 'aws', 'azure', 'gcp', 'serverless',
                    'container', 'docker', 'kubernetes', 'microservice',
                    'api', 'rest', 'graphql', 'database', 'storage'
                ],
                'ai_ml': [
                    'artificial intelligence', 'machine learning', 'deep learning',
                    'neural network', 'tensorflow', 'pytorch', 'scikit-learn',
                    'regression', 'classification', 'clustering', 'nlp',
                    'computer vision', 'reinforcement learning'
                ],
                'security': [
                    'security', 'cybersecurity', 'encryption', 'authentication',
                    'authorization', 'ssl', 'tls', 'vulnerability', 'attack',
                    'defense', 'penetration testing', 'firewall', 'antivirus'
                ]
            },
            'applications': {
                'industrial': [
                    'industrial', 'automation', 'control', 'plc', 'scada',
                    'manufacturing', 'production', 'quality', 'maintenance',
                    'predictive maintenance', 'condition monitoring'
                ],
                'smart_home': [
                    'smart home', 'home automation', 'smart device', 'voice control',
                    'smart lighting', 'smart security', 'smart thermostat',
                    'smart appliance', 'home assistant', 'voice assistant'
                ],
                'healthcare': [
                    'healthcare', 'medical', 'wearable', 'fitness', 'tracker',
                    'monitoring', 'diagnosis', 'treatment', 'telemedicine',
                    'medical device', 'health data', 'patient care'
                ],
                'transportation': [
                    'transportation', 'vehicle', 'automotive', 'autonomous',
                    'connected car', 'fleet management', 'traffic', 'navigation',
                    'logistics', 'supply chain', 'tracking', 'monitoring'
                ],
                'agriculture': [
                    'agriculture', 'farming', 'precision', 'irrigation',
                    'monitoring', 'automation', 'greenhouse', 'livestock',
                    'crop', 'soil', 'weather', 'climate', 'sustainability'
                ],
                'environment': [
                    'environment', 'monitoring', 'climate', 'weather',
                    'pollution', 'air quality', 'water quality', 'noise',
                    'conservation', 'sustainability', 'renewable energy'
                ]
            }
        }
        
        # Check for code-related keywords
        code_keywords = [
            'code', 'program', 'example', 'implement', 'write', 'show me',
            'how to', 'tutorial', 'demo', 'sample', 'sketch', 'script',
            'function', 'method', 'class', 'object', 'variable', 'constant',
            'loop', 'condition', 'statement', 'syntax', 'error', 'bug',
            'debug', 'test', 'compile', 'upload', 'flash', 'run'
        ]
        
        # Check for general explanation keywords
        explanation_keywords = [
            'what is', 'explain', 'describe', 'tell me about', 'meaning',
            'definition', 'overview', 'introduction', 'basics', 'how does',
            'why', 'when', 'where', 'which', 'compare', 'difference',
            'similarity', 'advantage', 'disadvantage', 'benefit', 'drawback'
        ]
        
        # Check for comparison keywords
        comparison_keywords = [
            'difference between', 'compare', 'vs', 'versus', 'which is better',
            'pros and cons', 'advantages and disadvantages', 'similarities',
            'differences', 'better than', 'worse than', 'prefer', 'choice',
            'selection', 'recommendation', 'suggestion', 'alternative'
        ]
        
        # Check for troubleshooting keywords
        troubleshooting_keywords = [
            'error', 'problem', 'issue', 'fix', 'solve', 'troubleshoot',
            'debug', 'not working', 'failed', 'crash', 'hang', 'freeze',
            'slow', 'performance', 'memory', 'resource', 'connection',
            'communication', 'network', 'hardware', 'software', 'compatibility'
        ]

        # Check if the question is related to any of our expertise areas
        is_related = False
        related_category = None
        
        # Check IoT core categories
        for category, keywords in keyword_categories['iot_core'].items():
            if any(keyword in message for keyword in keywords):
                is_related = True
                related_category = 'iot_core'
                break
        
        # Check related technology categories
        if not is_related:
            for category, keywords in keyword_categories['related_tech'].items():
                if any(keyword in message for keyword in keywords):
                    is_related = True
                    related_category = 'related_tech'
                    break
        
        # Check application categories
        if not is_related:
            for category, keywords in keyword_categories['applications'].items():
                if any(keyword in message for keyword in keywords):
                    is_related = True
                    related_category = 'applications'
                    break

        # If not directly related, check for technical context
        if not is_related:
            technical_context = any(word in message for word in [
                'technical', 'engineering', 'project', 'build', 'create',
                'develop', 'design', 'implement', 'solution', 'system',
                'device', 'application', 'product', 'prototype', 'technology',
                'innovation', 'research', 'development', 'science', 'engineering'
            ])
            
            if technical_context:
                return 'general'
            else:
                return 'non-technical'
        
        if any(keyword in message for keyword in code_keywords):
            return 'code'
        elif any(keyword in message for keyword in explanation_keywords):
            return 'explanation'
        elif any(keyword in message for keyword in comparison_keywords):
            return 'comparison'
        elif any(keyword in message for keyword in troubleshooting_keywords):
            return 'troubleshooting'
        else:
            return 'general'

    def get_response(self, message, model='meta-llama/Llama-4-Maverick-17B-128E-Instruct'):
        """Get response from the chatbot using the specified model"""
        try:
            # Check if the requested model is available
            if model not in self.available_models:
                return f"Error: Model '{model}' is not available. Please select from: {', '.join(self.available_models)}"
            
            # Check if it's a greeting
            if self.is_greeting(message):
                response = self.get_greeting_response()
                # Save greeting conversation
                self.db.save_conversation(message, response, model, 'greeting')
                return response
            
            # Analyze question type
            question_type = self.analyze_question_type(message)
            
            # Prepare the prompt with context
            prompt = f"{self.system_prompt}\n\nQuestion Type: {question_type}\nUser: {message}\nAssistant:"
            
            # Get response from the model
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Question Type: {question_type}\n{message}"}
                ],
                temperature=0.7,
                max_tokens=4096,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # If the response doesn't contain IoT-related keywords, add a note
            iot_keywords = [
                'iot', 'internet of things', 'embedded', 'esp32', 'arduino', 'raspberry pi',
                'sensor', 'actuator', 'mqtt', 'wifi', 'bluetooth', 'microcontroller',
                'circuit', 'electronics', 'hardware', 'firmware', 'protocol', 'wireless',
                'network', 'data', 'analytics', 'automation', 'control', 'monitoring',
                'device', 'system', 'programming', 'code', 'development', 'project'
            ]
            
            if not any(keyword in bot_response.lower() for keyword in iot_keywords):
                bot_response += "\n\nNote: While I can answer general questions, my primary expertise is in IoT and Embedded Systems. For the most accurate and detailed information, I recommend asking questions related to:\n" + \
                               "- IoT device development and programming\n" + \
                               "- Embedded systems design and implementation\n" + \
                               "- Sensor and actuator integration\n" + \
                               "- Wireless communication protocols\n" + \
                               "- Microcontroller programming\n" + \
                               "- Circuit design and electronics\n" + \
                               "- Data collection and analysis\n" + \
                               "- System automation and control"
            
            # Save the conversation to database
            self.db.save_conversation(message, bot_response, model, question_type)
            
            return bot_response
        
        except Exception as e:
            logging.error(f"Error getting response: {str(e)}")
            error_response = "I apologize, but I encountered an error while processing your request. Please try again."
            # Save error conversation
            self.db.save_conversation(message, error_response, model, 'error')
            return error_response

    def get_conversation_history(self, limit=10):
        """Get recent conversation history from database"""
        return self.db.get_conversation_history(limit)

    def __del__(self):
        """Cleanup database connection when object is destroyed"""
        if hasattr(self, 'db'):
            self.db.close()

def init_chatbot():
    global chatbot
    if chatbot is None:
        chatbot = IoTChatbot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/history', methods=['GET'])
def get_chat_history():
    init_chatbot()
    try:
        history = chatbot.get_conversation_history()
        return jsonify([{
            'id': chat[0],
            'user_message': chat[1],
            'bot_response': chat[2],
            'timestamp': chat[3].strftime('%Y-%m-%d %H:%M:%S'),
            'model_used': chat[4],
            'question_type': chat[5]
        } for chat in history])
    except Exception as e:
        logging.error(f"Error getting chat history: {str(e)}")
        return jsonify({'error': 'Failed to get chat history'}), 500

@app.route('/api/chat/<int:chat_id>', methods=['GET'])
def get_chat(chat_id):
    init_chatbot()
    try:
        # Get the specific chat from database
        db = Database()
        db.cursor.execute("""
            SELECT user_message, bot_response, timestamp, model_used, question_type
            FROM conversations
            WHERE id = %s
        """, (chat_id,))
        chat = db.cursor.fetchone()
        db.close()

        if chat:
            return jsonify({
                'id': chat_id,
                'messages': [
                    {'role': 'user', 'content': chat[0]},
                    {'role': 'assistant', 'content': chat[1]}
                ],
                'timestamp': chat[2].strftime('%Y-%m-%d %H:%M:%S'),
                'model_used': chat[3],
                'question_type': chat[4]
            })
        else:
            return jsonify({'error': 'Chat not found'}), 404
    except Exception as e:
        logging.error(f"Error getting chat: {str(e)}")
        return jsonify({'error': 'Failed to get chat'}), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    init_chatbot()
    try:
        data = request.json
        message = data.get('message')
        chat_id = data.get('chat_id')
        is_new_chat = data.get('is_new_chat', True)

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Get response from chatbot
        response = chatbot.get_response(message)
        
        # If it's a new chat, create a new conversation
        if is_new_chat:
            db = Database()
            db.cursor.execute("""
                INSERT INTO conversations (user_message, bot_response, model_used, question_type)
                VALUES (%s, %s, %s, %s)
            """, (message, response, 'meta-llama/Llama-4-Maverick-17B-128E-Instruct', 'general'))
            db.connection.commit()
            chat_id = db.cursor.lastrowid
            db.close()

        return jsonify({
            'response': response,
            'chat_id': chat_id
        })
    except Exception as e:
        logging.error(f"Error handling chat: {str(e)}")
        return jsonify({'error': 'Failed to process chat'}), 500

if __name__ == '__main__':
    app.run(debug=True) 