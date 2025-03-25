# Fulcrum Chat Application

A modern React-based chat interface for engineers, featuring a sleek design with a sidebar navigation and AI-powered chat functionality.

## Features

- User authentication with Firebase (login/signup)
- Dark/light theme toggle
- Responsive sidebar navigation with toggle functionality
- Real-time chat interface with AI responses
- Modern UI with smooth animations
- File upload capabilities
- PDF chat functionality

## Project Architecture

### Directory Structure
```
fulcrum/
├── frontend/               # React frontend application
│   ├── src/               # Source files
│   ├── public/            # Public assets
│   └── package.json       # Frontend dependencies
├── backend/
│   ├── API/              # Main API service
│   │   ├── requirements.txt
│   │   └── run_api.py
│   └── API_projects/     # Projects API service
│       ├── requirements.txt
│       └── run_api.py
└── .env                  # Environment variables (root level)
```

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- Python 3.8+
- npm or yarn
- Firebase account

### Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Add a web app to your project
4. Enable Authentication in the Firebase console:
   - Go to Authentication > Sign-in method
   - Enable Email/Password authentication
5. Copy your Firebase configuration (apiKey, authDomain, etc.)

## Local Development Setup

1. Clone the repository
2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Install backend dependencies:
```bash
# For main API
cd backend/API
pip install -r requirements.txt

# For projects API
cd backend/API_projects
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```
# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
FIREBASE_APP_ID=your_app_id

# Backend Configuration
API_KEY=your_api_key
OTHER_REQUIRED_VARIABLES=value
```

### Running Locally

You need to start three services:

1. Frontend:
```bash
cd frontend
npm run dev
```

2. Main API:
```bash
cd backend/API
python run_api.py
```

3. Projects API:
```bash
cd backend/API_projects
python run_api.py
```

## Replit Deployment Instructions

### Setting Up on Replit

1. Create a new Repl and choose "Import from GitHub"
2. Enter your repository URL
3. Select "Node.js" as the language

### Environment Setup in Replit

1. Go to the "Secrets" tab in your Repl
2. Add all environment variables from your `.env` file as secrets:
   - Click "New Secret" for each variable
   - Use the same variable names as in your `.env` file
   - Add all Firebase and backend configuration variables

### Configuration Steps

1. In the Replit shell, install all dependencies:
```bash
# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend/API
pip install -r requirements.txt
cd ../API_projects
pip install -r requirements.txt
```

2. Create a `.replit` file in the root directory with the following content:
```
run = "bash start.sh"
```

3. Create a `start.sh` file in the root directory:
```bash
#!/bin/bash
# Start frontend
cd frontend && npm run dev &
# Start main API
cd ../backend/API && python run_api.py &
# Start projects API
cd ../API_projects && python run_api.py &
wait
```

4. Make the start script executable:
```bash
chmod +x start.sh
```

### Running on Replit

1. Click the "Run" button in Replit
2. The application will start all three services automatically
3. Replit will provide you with a URL where your application is deployed

### Important Notes

- Ensure all environment variables are properly set in Replit's Secrets
- The frontend will run on the Replit-provided URL
- Backend services will run on different ports as configured in your API files
- Make sure to update any CORS settings in your backend to allow requests from your Replit domain

## Technologies Used

- React
- TypeScript
- Python (FastAPI)
- Firebase Authentication
- Styled Components
- React Router
- React Icons

## License

MIT
