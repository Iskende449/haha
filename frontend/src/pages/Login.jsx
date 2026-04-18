import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'
import { toApiErrorMessage } from '@/services/api'

export default function Login() {
  const navigate = useNavigate()
  const { loginMutation, registerMutation } = useAuth()
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [localError, setLocalError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLocalError(null)

    // Client-side validation
    if (isRegister) {
      if (!fullName || fullName.trim().length < 2) {
        setLocalError('Full name must be at least 2 characters.')
        return
      }
      if (!email) {
        setLocalError('Email is required.')
        return
      }
      if (password.length < 8) {
        setLocalError('Password must be at least 8 characters.')
        return
      }
    }

    try {
      if (isRegister) {
        // Register first, then login as a separate step
        await registerMutation.mutateAsync({ email, password, full_name: fullName.trim() })
        // Only login if register succeeded
        await loginMutation.mutateAsync({ email, password })
      } else {
        await loginMutation.mutateAsync({ email, password })
      }
      navigate('/')
    } catch {
      // Error is surfaced via mutation.error below
    }
  }

  const errorRaw = localError
    ? null
    : loginMutation.error || registerMutation.error
  const error = localError || (errorRaw ? toApiErrorMessage(errorRaw) : null)

  const isLoading = loginMutation.isPending || registerMutation.isPending

  return (
    <div className='flex min-h-screen items-center justify-center px-5 py-10'>
      <div className='w-full max-w-sm'>
        {/* Logo / branding */}
        <div className='mb-8 text-center'>
          <div className='mb-3 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-700 text-3xl shadow-lg'>
            🏔️
          </div>
          <h1 className='text-2xl font-bold text-white'>Nomad Heritage</h1>
          <p className='mt-1 text-sm text-white/60'>Sacred Sites of Kyrgyzstan</p>
        </div>

        <div className='glass rounded-3xl p-6'>
          {/* Tab switcher */}
          <div className='mb-6 flex rounded-xl bg-white/5 p-1'>
            <button
              type='button'
              onClick={() => { setIsRegister(false); setLocalError(null) }}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all ${!isRegister ? 'bg-amber-500 text-black shadow' : 'text-white/60 hover:text-white'
                }`}
            >
              Login
            </button>
            <button
              type='button'
              onClick={() => { setIsRegister(true); setLocalError(null) }}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all ${isRegister ? 'bg-amber-500 text-black shadow' : 'text-white/60 hover:text-white'
                }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className='space-y-3'>
            {isRegister && (
              <div>
                <label className='mb-1 block text-xs text-white/60'>Full Name</label>
                <Input
                  placeholder='Аскар Матанов'
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete='name'
                  minLength={2}
                />
              </div>
            )}

            <div>
              <label className='mb-1 block text-xs text-white/60'>Email</label>
              <Input
                type='email'
                placeholder='your@email.com'
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete='email'
              />
            </div>

            <div>
              <label className='mb-1 block text-xs text-white/60'>
                Password {isRegister && <span className='text-white/40'>(min 8 chars)</span>}
              </label>
              <Input
                type='password'
                placeholder='••••••••'
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={isRegister ? 'new-password' : 'current-password'}
              />
            </div>

            {error && <div className='rounded-xl bg-red-500/15 px-3 py-2 text-xs text-red-300'>{error}</div>}

            <Button
              type='submit'
              className='mt-2 w-full bg-amber-500 font-semibold text-black hover:bg-amber-400'
              disabled={isLoading}
            >
              {isLoading
                ? '...'
                : isRegister
                  ? '🚀 Create Account & Enter'
                  : '🏔️ Enter the Path'}
            </Button>
          </form>

          <p className='mt-5 text-center text-[11px] text-white/30'>
            By entering, you follow the path of ancestors.
          </p>
        </div>
      </div>
    </div>
  )
}
