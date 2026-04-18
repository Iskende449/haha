import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/services/api'

export function useExplorerLocations() {
  return useQuery({
    queryKey: ['explorer', 'locations'],
    queryFn: async () => {
      const { data } = await api.get('/explorer/locations')
      return data
    },
  })
}

export function useExplorerLocation(sourceId) {
  return useQuery({
    queryKey: ['explorer', 'location', sourceId],
    enabled: Boolean(sourceId),
    queryFn: async () => {
      const { data } = await api.get(`/explorer/locations/${sourceId}`)
      return data
    },
  })
}

export function useExplorerRoute() {
  return useMutation({
    mutationFn: async ({ source_id, user_lat, user_lon, transport_mode, locale }) => {
      const { data } = await api.post('/explorer/route', {
        source_id,
        user_lat,
        user_lon,
        transport_mode,
        locale,
        route_style: 'smart',
      })
      return data
    },
  })
}
