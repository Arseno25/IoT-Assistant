# IoT Assistant

A real-time chat application powered by AI, specifically designed for IoT and Embedded Systems development. This application provides instant assistance for hardware development, IoT protocols, data analysis, and AI integration.

![IoT Assistant Screenshot](screenshot.png)

## Features

### Core Features
- 🤖 AI-powered chat interface for IoT and Embedded Systems
- 💬 Real-time messaging with WebSocket support
- 📱 Responsive design for all devices
- 🔒 User authentication and session management
- 💾 Chat history saving for registered users
- 🎨 Modern and intuitive user interface

### Technical Capabilities
- Hardware Development (ESP32, Arduino, Raspberry Pi)
- IoT Protocols (MQTT, HTTP, WebSocket)
- Data Analysis and Visualization
- AI and Machine Learning Integration
- Code Implementation Support
- System Optimization Guidance

## Tech Stack

### Backend
- Python 3.8+
- Flask (Web Framework)
- Flask-SocketIO (Real-time communication)
- SQLAlchemy (Database ORM)
- MySQL (Database)
- Python-dotenv (Environment management)

### Frontend
- HTML5
- CSS3 (with modern features)
- JavaScript (ES6+)
- Socket.IO Client
- Bootstrap 5
- Font Awesome Icons
- Highlight.js (Code syntax highlighting)
- Marked.js (Markdown rendering)

## Installation

### Prerequisites
- Python 3.8 or higher
- MySQL Server
- Node.js (for development tools)

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/iotassist.git
cd iotassist
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```env
SECRET_KEY=your_secret_key
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_NAME=iotassist
```

5. Initialize the database:
```bash
python init_db.py
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
iotassist/
├── app.py                 # Main application file
├── database.py            # Database models and operations
├── iot_chatbot.py         # AI chatbot implementation
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── static/               # Static files
│   ├── css/
│   ├── js/
│   └── images/
└── templates/            # HTML templates
    ├── index.html
    ├── login.html
    ├── register.html
    └── settings.html
```

## Usage

### Guest Users
- Access the chat interface without registration
- Get instant AI responses
- Try out the system before registering
- Note: Chat history is not saved for guest users

### Registered Users
- Full access to all features
- Chat history saving
- Profile customization
- Settings management
- Account security

### Quick Actions
- MQTT with ESP32
- IoT Protocols
- Sensor Data Analysis

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
This project follows PEP 8 guidelines. Use the following tools:
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linter
flake8 .

# Run formatter
black .
```

### Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Security

- Password hashing using Werkzeug
- Session management with Flask-Session
- CSRF protection
- Secure headers
- Input validation
- SQL injection prevention

## Performance

- WebSocket for real-time communication
- Database indexing for faster queries
- Caching for frequently accessed data
- Optimized asset loading
- Responsive image handling

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask team for the amazing web framework
- Socket.IO for real-time capabilities
- Bootstrap for the UI framework
- Font Awesome for the icons
- All contributors and users

## Support

For support, please:
1. Check the [documentation](docs/)
2. Search for existing issues
3. Create a new issue if needed

## Roadmap

- [ ] Mobile app development
- [ ] Multi-language support
- [ ] Advanced code analysis
- [ ] Hardware simulation
- [ ] API documentation
- [ ] Community features

## Contact

Project Maintainer: [Arseno25](mailto:mrshadow2511@gmail.com)

Project Link: [https://github.com/Arseno25/iotassist](https://github.com/Arseno25/iotassist) 