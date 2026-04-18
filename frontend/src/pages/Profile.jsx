import { Gem, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'

const mockLegends = [
  'Saimaluu-Tash Sun Hunter',
  'Burana Whisper Keeper',
  'Manjyly-Ata Spring Oath',
]

export default function Profile() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <div className='min-h-screen px-4 py-5'>
      <h1 className='mb-1 text-xl font-semibold text-gold'>Profile & Progress</h1>
      <p className='mb-5 text-sm text-white/70'>{user?.full_name || 'Nomad Traveler'}</p>

      <div className='glass mb-4 rounded-2xl p-4'>
        <p className='text-xs text-white/70'>Experience</p>
        <p className='text-2xl font-semibold text-emerald-300'>{user?.experience_points ?? 0} XP</p>
      </div>

      <h2 className='mb-2 text-sm font-semibold text-white'>Unlocked Legends</h2>
      <div className='space-y-2'>
        {mockLegends.map((legend) => (
          <div key={legend} className='glass flex items-center gap-2 rounded-xl p-3'>
            <Gem size={16} className='text-gold' />
            <span className='text-sm'>{legend}</span>
          </div>
        ))}
      </div>

      <div className='mt-5 flex gap-2'>
        <Button variant='ghost' onClick={() => navigate('/')}>Back to map</Button>
        <Button variant='ghost' onClick={logout}>
          <LogOut size={14} className='mr-1' />
          Logout
        </Button>
      </div>
    </div>
  )
}
