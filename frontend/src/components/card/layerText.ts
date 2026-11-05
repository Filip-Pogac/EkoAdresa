import type { LayerName, Layers } from '../../api/types';
import { hr } from '../../i18n/hr';

export const LAYER_ORDER: LayerName[] = ['flood', 'noise', 'air', 'waste', 'mobility'];

/** Plain Croatian sentences for a layer: [main sentence, ...notes (data age etc.)]. */
export function layerSentences(name: LayerName, layers: Layers): string[] {
  switch (name) {
    case 'flood': {
      const l = layers.flood;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.flood.sentence(l)];
    }
    case 'noise': {
      const l = layers.noise;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.noise.sentence(l)];
    }
    case 'air': {
      const l = layers.air;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [
            hr.layers.air.sentence(l),
            hr.layers.air.period(l),
            ...(l.dhmz && l.dhmz.values.length ? [hr.layers.air.dhmz(l.dhmz)] : []),
          ];
    }
    case 'waste': {
      const l = layers.waste;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.waste.sentence(l), hr.layers.waste.period()];
    }
    case 'mobility': {
      const l = layers.mobility;
      return l.status === 'unavailable'
        ? [hr.layers.unavailable(l)]
        : [hr.layers.mobility.sentence(l)];
    }
  }
}
