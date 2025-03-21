'use client';

import { useRouter } from 'next/navigation';
import FullPageChat from '../components/FullPageChat';

export default function ChatPage() {
  const router = useRouter();
  
  const handleClose = () => {
    router.push('/');
  };

  return <FullPageChat onClose={handleClose} />;
} 