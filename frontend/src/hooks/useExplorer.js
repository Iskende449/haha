import { useMutation, useQuery } from '@tanstack/react-query'

import { api } from '@/services/api'

export function useExplorerBootstrap() {
  return useQuery({
    queryKey: ['explorer', 'bootstrap'],
    queryFn: async () => {
      const { data } = await api.get('/explorer/bootstrap')
      return data
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function useExplorerLocations(filters = {}) {
  return useQuery({
    queryKey: ['explorer', 'locations', filters],
    queryFn: async () => {
      const { data } = await api.get('/explorer/locations', { params: filters })
      return data
    },
  })
}

export function useExplorerLocation(sourceId, params = {}) {
  return useQuery({
    queryKey: ['explorer', 'location', sourceId, params],
    enabled: Boolean(sourceId),
    queryFn: async () => {
      const { data } = await api.get(`/explorer/locations/${sourceId}`, { params })
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
