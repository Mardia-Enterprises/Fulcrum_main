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
3. Add the following additional environment variables for API URLs:
   ```
   VITE_API_URL=https://fulcrumapp.replit.app
   VITE_PROJECT_API_URL=https://fulcrumapp.replit.app
   ```

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
modules = ["python-3.12", "nodejs-20", "bash", "nodejs-23"]
run = "bash start.sh"

[nix]
channel = "stable-24_05"

[deployment]
run = ["sh", "-c", "bash start.sh"]
build = ["sh", "-c", "cd frontend && npm install"]

[[ports]]
localPort = 3000
externalPort = 80

[[ports]]
localPort = 3001

[[ports]]
localPort = 8000
externalPort = 8000

[[ports]]
localPort = 8001
externalPort = 3000
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

### Port Configuration in Replit

The port configuration in the `.replit` file maps the services as follows:

- Frontend (Vite): 
  - Local port: 3000
  - External port: 80 (main application URL)
- Main API:
  - Local port: 8000
  - External port: 8000
- Projects API:
  - Local port: 8001
  - External port: 3000
- Additional port 3001 for other services

### API URL Configuration

When deploying to Replit, ensure that:

1. All API calls in the frontend code use environment variables instead of hardcoded localhost URLs:
   ```javascript
   // Instead of:
   // fetch('http://localhost:8000/api/...)
   
   // Use:
   fetch(`${import.meta.env.VITE_API_URL}:8000/api/...`)
   ```

2. Update CORS settings in both API services to allow requests from your Replit domain:
   ```python
   origins = [
       "https://fulcrumapp.replit.app",
       "http://localhost:3000",  # Keep for local development
   ]
   ```

### Running on Replit

1. Click the "Run" button in Replit
2. The application will start all three services automatically
3. Access your application at `https://fulcrumapp.replit.app`

### Important Notes

- Ensure all environment variables are properly set in Replit's Secrets
- The frontend will be accessible at the main Replit URL (https://fulcrumapp.replit.app)
- API services will be accessible at:
  - Main API: https://fulcrumapp.replit.app:8000
  - Projects API: https://fulcrumapp.replit.app:3000
- Double-check all API calls in the frontend code to ensure they use environment variables
- Monitor the Replit console for any port-related errors
- If you encounter CORS issues, verify that the CORS configuration in both APIs includes your Replit domain

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
