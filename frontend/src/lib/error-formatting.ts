/** Extract the first human-readable field or non-field error message from DRF serializer payloads. */
export function formatSerializerErrors(details: unknown, fallback: string): string {
  if (!details || typeof details !== "object") {
    return fallback;
  }
  const record = details as Record<string, unknown>;
  for (const value of Object.values(record)) {
    if (Array.isArray(value) && typeof value[0] === "string") {
      return value[0];
    }
    if (typeof value === "string") {
      return value;
    }
  }
  return fallback;
}
