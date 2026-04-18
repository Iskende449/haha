import { useMutation } from '@tanstack/react-query'

import { api } from '@/services/api'

export function useRouteGenerator() {
  return useMutation({
    mutationFn: async ({ user_lon, user_lat, transport_type, duration_hours, interests, destination_name }) => {
      const { data } = await api.post('/route', {
        user_lon,
        user_lat,
        transport_type,
        duration_hours,
        interests,
        destination_name,
      })
      return data
    },
  })
}

export function useCheckIn() {
  return useMutation({
    mutationFn: async ({ location_id, user_lon, user_lat, legend_answer }) => {
      const { data } = await api.post('/checkin', {
        location_id,
        user_lon,
        user_lat,
        legend_answer,
      })
      return data
    },
  })
}
