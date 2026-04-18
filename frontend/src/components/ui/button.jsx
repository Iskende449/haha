import { cn } from '@/lib/utils'

export function Button({ className, variant = 'default', ...props }) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition-all active:scale-[0.98]',
        variant === 'default' && 'bg-gold text-black hover:brightness-105',
        variant === 'ghost' && 'bg-white/10 text-white hover:bg-white/20',
        variant === 'emerald' && 'bg-emerald text-white hover:brightness-110',
        className,
      )}
      {...props}
    />
  )
}
