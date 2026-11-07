import type { maplibregl } from '../map/maplibre';

/** EkoSkor classes for the city map, worst to best: red, orange, yellow, light green, dark
 * green (ColorBrewer RdYlGn, 5 classes). Only for the city map; the traffic-light colours on
 * the address card are for layer status. */
export const HEATMAP_CLASSES = [
  { from: 0, to: 20, colour: '#d73027' },
  { from: 21, to: 40, colour: '#fc8d59' },
  { from: 41, to: 60, colour: '#fee08b' },
  { from: 61, to: 80, colour: '#91cf60' },
  { from: 81, to: 100, colour: '#1a9850' },
];

const [lowest, ...higher] = HEATMAP_CLASSES;

/** MapLibre `step` expression: colour of the class the cell's EkoSkor falls in. */
export const FILL_COLOUR: maplibregl.ExpressionSpecification = [
  'step',
  ['get', 'ekoskor'],
  lowest?.colour ?? '#ffffcc',
  ...higher.flatMap((c) => [c.from, c.colour]),
];
