'use client';

import { useRouter } from 'next/navigation';

export default function ChatButton() {
  const router = useRouter();

  const navigateToChat = () => {
    router.push('/chat');
  };

  return (
    <button
      onClick={navigateToChat}
      className="fixed bottom-5 right-5 bg-blue-600 hover:bg-blue-700 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg transition-all z-40"
      aria-label="Open Project Assistant Chat"
    >
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
      </svg>
    </button>
  );
} 