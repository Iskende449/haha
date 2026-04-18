import { Sparkles } from 'lucide-react'

export function AncestorsVoiceWidget({ nomadicMonth, blessing, onSpeak }) {
  return (
    <div className='glass absolute left-4 right-4 top-4 z-[1000] rounded-2xl p-4'>
      <div className='mb-2 flex items-center justify-between'>
        <div className='flex items-center gap-2 text-gold'>
          <Sparkles size={18} />
          <p className='text-sm font-semibold'>Ancestors&apos; Voice</p>
        </div>
        <button className='text-xs text-white/80 underline' onClick={onSpeak}>
          Speak
        </button>
      </div>
      <p className='text-xs text-emerald-300'>Nomadic Month: {nomadicMonth}</p>
      <p className='mt-2 text-sm text-white/90'>{blessing}</p>
    </div>
  )
}
