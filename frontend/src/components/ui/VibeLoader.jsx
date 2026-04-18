export function VibeLoader({ label = 'Consulting the ancestors...' }) {
  return (
    <div className='absolute inset-0 z-[1400] grid place-items-center bg-black/55'>
      <div className='rounded-[26px] border border-white/10 bg-[rgba(18,13,11,0.88)] px-6 py-5 text-center shadow-[0_20px_60px_rgba(0,0,0,0.48)] backdrop-blur-xl'>
        <div className='vibe-spinner mx-auto mb-3 h-10 w-10 rounded-full border-2 border-[#ffb366] border-t-transparent' />
        <p className='text-sm text-white'>{label}</p>
      </div>
    </div>
  )
}
