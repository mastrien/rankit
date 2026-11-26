import { ApiClient } from "./api-client";

export interface BackendHealthResponse {
  readonly status: "ok" | "degraded";
  readonly database: "ok" | "error";
}

function isBackendHealthResponse(value: unknown): value is BackendHealthResponse {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  const validStatus = record.status === "ok" || record.status === "degraded";
  const validDb = record.database === "ok" || record.database === "error";
  return validStatus && validDb;
}

/** Query the Django backend readiness endpoint and validate its response shape. */
export async function fetchBackendHealth(
  client: ApiClient = new ApiClient(),
): Promise<BackendHealthResponse> {
  const payload = await client.get<unknown>("/api/v1/health/");
  if (!isBackendHealthResponse(payload)) {
    throw new Error(
      `Invalid backend health payload: ${JSON.stringify(payload)} (expected {status, database}).`,
    );
  }
  return payload;
}
