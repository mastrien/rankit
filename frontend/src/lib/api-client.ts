export interface ApiErrorShape {
  readonly status: number;
  readonly url: string;
  readonly message: string;
  readonly details: unknown;
}

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly url: string;
  public readonly details: unknown;

  constructor({ status, url, message, details }: ApiErrorShape) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.url = url;
    this.details = details;
  }
}

export type FetchLike = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

const DEFAULT_PUBLIC_API_URL = "http://localhost:8000";

/** Resolve the base backend URL depending on browser vs server runtime. */
export function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_PUBLIC_API_URL;
  }
  return process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_PUBLIC_API_URL;
}

function extractErrorMessage(payload: unknown, fallbackStatus: number, url: string): string {
  if (payload && typeof payload === "object") {
    const record = payload as Record<string, unknown>;
    if (typeof record.detail === "string") {
      return record.detail;
    }
    if (typeof record.message === "string") {
      return record.message;
    }
  }
  return `Request to ${url} failed with HTTP status ${fallbackStatus} (expected 2xx JSON response).`;
}

/** Thin typed HTTP client wrapping fetch with cookie credentials and structured errors. */
export class ApiClient {
  private readonly baseUrl: string;
  private readonly fetchFn: FetchLike;

  constructor(baseUrl: string = resolveApiBaseUrl(), fetchFn?: FetchLike) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    // Bind global fetch so browser engines do not throw Illegal invocation on method call.
    this.fetchFn = fetchFn ?? ((input, init) => globalThis.fetch(input, init));
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
    const headers = new Headers(init.headers);
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await this.fetchFn(url, {
      ...init,
      headers,
      credentials: "include",
    });

    const contentType = response.headers.get("content-type") ?? "";
    const isJson = contentType.includes("application/json");
    const payload = isJson && response.status !== 204 ? await response.json() : null;

    if (!response.ok) {
      throw new ApiClientError({
        status: response.status,
        url,
        message: extractErrorMessage(payload, response.status, url),
        details: payload,
      });
    }

    return payload as T;
  }

  get<T>(path: string, init: RequestInit = {}): Promise<T> {
    return this.request<T>(path, { ...init, method: "GET" });
  }

  post<T>(path: string, body?: unknown, init: RequestInit = {}): Promise<T> {
    return this.request<T>(path, {
      ...init,
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  }

  patch<T>(path: string, body: unknown, init: RequestInit = {}): Promise<T> {
    return this.request<T>(path, {
      ...init,
      method: "PATCH",
      body: JSON.stringify(body),
    });
  }

  delete<T>(path: string, init: RequestInit = {}): Promise<T> {
    return this.request<T>(path, { ...init, method: "DELETE" });
  }
}
