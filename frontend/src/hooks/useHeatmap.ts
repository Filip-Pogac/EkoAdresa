import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export function useHeatmap() {
  return useQuery({
    queryKey: ['heatmap'],
    queryFn: ({ signal }) => api.heatmap(signal),
    staleTime: Infinity, // committed snapshot
  });
}
