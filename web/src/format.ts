export function percent(value: number | null | undefined, digits = 1, signed = false): string {
  if (value == null || Number.isNaN(value)) return "—";
  const text = `${Math.abs(value * 100).toFixed(digits)}%`;
  if (value < 0) return `−${text}`;
  return signed && value > 0 ? `+${text}` : text;
}

export function number(value: number | null | undefined, digits = 0): string {
  if (value == null || Number.isNaN(value)) return "—";
  const text = Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  return value < 0 ? `−${text}` : text;
}

export function ratio(value: number | null | undefined): string {
  return number(value, 2);
}

export function day(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export function shortDay(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { day: "numeric", month: "short", timeZone: "UTC" });
}

export function monthLabel(key: string): string {
  return new Date(`${key}-01T00:00:00Z`).toLocaleDateString("en-US", { month: "short", year: "2-digit", timeZone: "UTC" });
}

export function stamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit", timeZone: "UTC" }) + " UTC";
}

export const SERIES = ["#0f9d63", "#2563eb", "#d97706", "#db2777", "#7c3aed"];

/** A value with its unit, e.g. "3.0% year over year" or "1,000 USD million". */
export function withUnit(value: number, unit: string): string {
  if (unit.startsWith("%")) return `${value.toFixed(1)}%${unit.slice(1)}`;
  return `${number(value, Number.isInteger(value) ? 0 : 1)} ${unit}`;
}

/** Up to two decimals, but no trailing zeros beyond one: 4.25 → "4.25", 3 → "3.0". */
export function rate(value: number): string {
  return value.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 2 });
}
