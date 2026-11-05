/** Croatian number, distance and date formatting (decimal comma, "1,2 km"). */

const number1 = new Intl.NumberFormat('hr-HR', { maximumFractionDigits: 1 });
const dateLong = new Intl.DateTimeFormat('hr-HR', {
  day: 'numeric',
  month: 'numeric',
  year: 'numeric',
});

export function formatNumber(value: number): string {
  return number1.format(value);
}

export function formatDistance(distanceM: number): string {
  if (distanceM < 1000) return `${Math.round(distanceM)} m`;
  return `${number1.format(distanceM / 1000)} km`;
}

/** 'YYYY-MM-DD' or ISO 8601 -> '31. 8. 2023.' */
export function formatDate(iso: string): string {
  const date = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? new Date(`${iso}T12:00:00`) : new Date(iso);
  return dateLong.format(date);
}
