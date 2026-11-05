import type { maplibregl } from '../map/maplibre';

/** EkoSkor classes for the city map: sequential ColorBrewer YlGn (colour-blind safe). Not the
 * traffic-light colours, which are reserved for layer status on the address card. */
export const HEATMAP_CLASSES = [
  { from: 0, to: 20, colour: '#ffffcc' },
  { from: 21, to: 40, colour: '#c2e699' },
  { from: 41, to: 60, colour: '#78c679' },
  { from: 61, to: 80, colour: '#31a354' },
  { from: 81, to: 100, colour: '#006837' },
];

const [lowest, ...higher] = HEATMAP_CLASSES;

/** MapLibre `step` expression: colour of the class the cell's EkoSkor falls in. */
export const FILL_COLOUR: maplibregl.ExpressionSpecification = [
  'step',
  ['get', 'ekoskor'],
  lowest?.colour ?? '#ffffcc',
  ...higher.flatMap((c) => [c.from, c.colour]),
];
