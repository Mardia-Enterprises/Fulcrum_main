import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chat - Project Assistant',
  description: 'Ask questions about our projects and team members',
}

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="h-full">
      {children}
    </div>
  )
} 