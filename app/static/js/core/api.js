"use strict";

export class ApiError extends Error {
    constructor(message, options = {}) {
        super(message);
        this.name = "ApiError";
        this.status = options.status ?? null;
        this.payload = options.payload ?? null;
        this.code = options.code ?? null;
    }
}

function buildQueryParams(filters = {}) {
    const params = new URLSearchParams();

    const mappings = {
        client: "client",
        problem: "problem",
        priority: "priority",
        technician: "technician",
        dateFrom: "date_from",
        dateTo: "date_to",
    };

    for (const [stateKey, queryKey] of Object.entries(mappings)) {
        const value = filters[stateKey];

        if (value === null || value === undefined) {
            continue;
        }

        const normalized = String(value).trim();

        if (!normalized) {
            continue;
        }

        if (normalized.toUpperCase() === "ALL") {
            continue;
        }

        params.set(queryKey, normalized);
    }

    return params;
}

export class ApiClient {
    constructor({ baseUrl = "/api", timeoutMs = 10000 } = {}) {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        this.timeoutMs = timeoutMs;
    }

    async request(
        path,
        { method = "GET", headers = {}, body = null, signal = null } = {},
    ) {
        if (signal?.aborted) {
            throw new ApiError("API request was cancelled.", {
                code: "REQUEST_CANCELLED",
            });
        }

        const controller = new AbortController();
        let timedOut = false;
        let cancelled = false;
        const abortFromCaller = () => {
            cancelled = true;
            controller.abort();
        };
        signal?.addEventListener("abort", abortFromCaller, { once: true });
        const timeoutId = window.setTimeout(() => {
            timedOut = true;
            controller.abort();
        }, this.timeoutMs);

        try {
            const response = await fetch(`${this.baseUrl}${path}`, {
                method,
                headers: {
                    "Accept": "application/json",
                    ...headers,
                },
                body,
                signal: controller.signal,
            });

            const contentType = response.headers.get("content-type") ?? "";
            const payload = contentType.includes("application/json")
                ? await response.json()
                : await response.text();

            if (!response.ok) {
                throw new ApiError(
                    `API request failed with HTTP ${response.status}`,
                    { status: response.status, payload }
                );
            }

            return payload;
        } catch (error) {
            if (timedOut) {
                throw new ApiError("API request timed out.");
            }
            if (cancelled || signal?.aborted) {
                throw new ApiError("API request was cancelled.", {
                    code: "REQUEST_CANCELLED",
                });
            }
            if (error instanceof ApiError) {
                throw error;
            }
            throw new ApiError(
                "Unable to communicate with the API.",
                { payload: error }
            );
        } finally {
            window.clearTimeout(timeoutId);
            signal?.removeEventListener("abort", abortFromCaller);
        }
    }

    get(path, { query = null, signal = null } = {}) {
        if (!query) {
            return this.request(path, { signal });
        }

        const params = buildQueryParams(query);
        const queryString = params.toString();

        if (!queryString) {
            return this.request(path, { signal });
        }

        const separator = path.includes("?") ? "&" : "?";
        return this.request(`${path}${separator}${queryString}`, { signal });
    }
}

export { buildQueryParams };
export const apiClient = new ApiClient();
