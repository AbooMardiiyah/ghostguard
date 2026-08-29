import { useState } from 'react'
import Shell, { type SectionKey } from '@/components/Shell'
import Login from '@/sections/Login'
import CommandCenter from '@/sections/CommandCenter'
import LiveDefense from '@/sections/LiveDefense'
import Integrations from '@/sections/Integrations'
import AuditTrail from '@/sections/AuditTrail'
import Scheduler from '@/sections/Scheduler'

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [section, setSection] = useState<SectionKey>('command')

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />

  return (
    <Shell active={section} onNavigate={setSection} onSignOut={() => setLoggedIn(false)}>
      {section === 'command' && <CommandCenter />}
      {section === 'defense' && <LiveDefense />}
      {section === 'integrations' && <Integrations />}
      {section === 'scheduler' && <Scheduler />}
      {section === 'audit' && <AuditTrail />}
    </Shell>
  )
}
