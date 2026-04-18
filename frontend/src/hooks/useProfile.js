import { useQuery } from '@tanstack/react-query'

import { api } from '@/services/api'

export function useProfile(enabled = true) {
  return useQuery({
    queryKey: ['profile'],
    enabled,
    queryFn: async () => {
      const { data } = await api.get('/profile')
      return data
    },
  })
}
