import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { hr } from '../i18n/hr';
import type { Place } from '../routes';

/**
 * Title for a place: the typed address if there is one; for a point picked on the map, the
 * nearest address (within 150 m, /api/reverse) with a note on its distance, else the named
 * park or forest the point is in; otherwise the generic "point on the map". While the lookup
 * runs, or if it fails, the generic title shows.
 */
export function usePlaceTitle(place: Place): { title: string; note: string | null } {
  const picked = place.label === null;
  const { data } = useQuery({
    queryKey: ['reverse', place.lat, place.lon],
    queryFn: ({ signal }) => api.reverse(place.lat, place.lon, signal),
    enabled: picked,
    staleTime: Infinity, // the address index is a fixed snapshot
  });
  if (!picked) return { title: place.label ?? '', note: null };
  const nearest = data?.result;
  if (!nearest) return { title: hr.card.pinnedPoint, note: null };
  if (nearest.kind === 'green_area') return { title: nearest.label, note: hr.card.greenAreaNote };
  return { title: nearest.label, note: hr.card.nearestNote(nearest.distance_m) };
}
