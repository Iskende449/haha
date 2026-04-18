import { Drawer } from 'vaul'
import { Car, Bike, Footprints, WandSparkles } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const transports = [
  { id: 'car', label: 'Car', icon: Car },
  { id: 'bike', label: 'Bike', icon: Bike },
  { id: 'foot', label: 'Foot', icon: Footprints },
]

export function RouteDrawer({
  open,
  setOpen,
  transport,
  setTransport,
  duration,
  setDuration,
  destinationName,
  setDestinationName,
  onSubmit,
  isLoading,
}) {
  return (
    <Drawer.Root open={open} onOpenChange={setOpen}>
      <Drawer.Portal>
        <Drawer.Overlay className='fixed inset-0 z-[1200] bg-black/60' />
        <Drawer.Content className='fixed bottom-0 left-0 right-0 z-[1300] mt-24 rounded-t-3xl border border-white/10 bg-panel p-5'>
          <div className='mx-auto mb-4 h-1.5 w-12 rounded-full bg-white/30' />
          <h3 className='mb-3 text-base font-semibold text-white'>Route Generator</h3>

          <Input
            placeholder='Destination hint (e.g., Burana)'
            value={destinationName}
            onChange={(e) => setDestinationName(e.target.value)}
            className='mb-4'
          />

          <div className='mb-4 grid grid-cols-3 gap-2'>
            {transports.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setTransport(item.id)}
                  className={`rounded-xl border px-3 py-3 text-sm ${
                    transport === item.id ? 'border-gold bg-gold/20 text-gold' : 'border-white/15 bg-white/5 text-white'
                  }`}
                >
                  <Icon className='mx-auto mb-1' size={18} />
                  {item.label}
                </button>
              )
            })}
          </div>

          <label className='mb-2 block text-xs text-white/70'>Duration: {duration}h</label>
          <input
            type='range'
            min='1'
            max='12'
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className='mb-5 w-full accent-[#D4AF37]'
          />

          <Button onClick={onSubmit} className='w-full' disabled={isLoading}>
            <WandSparkles className='mr-2' size={16} />
            {isLoading ? 'Vibe-Checking...' : 'Get Route'}
          </Button>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  )
}
