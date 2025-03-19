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

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
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
6. Update the `.env` file with your Firebase configuration values

### Installation

1. Clone the repository
2. Install dependencies:

```bash
cd engiverse-chat
npm install
```

3. Create a `.env` file based on `.env.example` and add your Firebase configuration:

```
REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

### Running the Application

```bash
npm start
```

The application will be available at [http://localhost:3000](http://localhost:3000).

### Building for Production

```bash
npm run build
```

## Technologies Used

- React
- TypeScript
- Firebase Authentication
- Styled Components
- React Router
- React Icons

## License

MIT
