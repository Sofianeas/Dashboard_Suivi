"use strict";

import { apiClient } from "./core/api.js";
import { store } from "./core/state.js";
import { bindRegistryEvents } from "./reference-registry.js";
import {
    getDashboardFilterValues,
    populateDashboardFilters,
    renderDashboard,
    renderDashboardError,
    resetDashboardFilterInputs,
    setDashboardFilterCatalogState,
    setApiStatus,
    setApplicationReady,
    setDashboardLoading,
} from "./core/ui.js";

let latestDashboardRequest = 0;
let activeDashboardController = null;
let dashboardFilterDebounceTimer = null;
let dashboardCatalog = null;
let dashboardCatalogError = null;
let dashboardCatalogPromise = null;

const DASHBOARD_FILTER_DEBOUNCE_MS = 200;

const EMPTY_DASHBOARD_FILTERS = Object.freeze({
    dateFrom: null,
    dateTo: null,
    client: null,
    problem: null,
    priority: null,
    technician: null,
});

function validateDashboardPayload(data) {
    const dimensionFields = {
        clients: "client",
        problems: "problem",
        priorities: "priority",
        technicians: "technician",
        temporal: "period",
    };

    if (
        !data ||
        typeof data !== "object" ||
        !data.kpi ||
        !Number.isFinite(data.kpi.ticket_count) ||
        !(
            data.kpi.mean_resolution_minutes === null ||
            Number.isFinite(data.kpi.mean_resolution_minutes)
        ) ||
        !(
            data.kpi.median_resolution_minutes === null ||
            Number.isFinite(data.kpi.median_resolution_minutes)
        )
    ) {
        throw new Error("La réponse KPI de l’API ne respecte pas le contrat attendu.");
    }

    for (const [key, field] of Object.entries(dimensionFields)) {
        if (
            !Array.isArray(data[key]) ||
            data[key].some((row) => (
                !row ||
                typeof row !== "object" ||
                !(field in row) ||
                !Number.isFinite(row.ticket_count) ||
                !(
                    row.mean_resolution_minutes === null ||
                    Number.isFinite(row.mean_resolution_minutes)
                )
            ))
        ) {
            throw new Error(`La réponse ${key} de l’API ne respecte pas le contrat attendu.`);
        }
    }

    return data;
}

function dashboardErrorMessage(error) {
    const detail = error?.payload?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        return detail
            .map((item) => item?.msg)
            .filter(Boolean)
            .join(" ");
    }
    if (error?.message === "API request timed out.") {
        return "La requête a dépassé le délai autorisé. Réessayez.";
    }
    if (error?.status === null || error?.status === undefined) {
        return "Impossible de joindre l’API. Vérifiez la connexion puis réessayez.";
    }
    return `L’API a répondu avec une erreur HTTP ${error.status}.`;
}

async function checkApiHealth() {
    setApiStatus("loading");

    try {
        const health = await apiClient.get("/health");

        if (health.status !== "ok") {
            throw new Error("Réponse de santé inattendue.");
        }

        store.setState((state) => ({
            ...state,
            application: {
                ...state.application,
                apiAvailable: true,
            },
        }));

        setApiStatus("success");
        return true;
    } catch (error) {
        console.error("API health check failed:", error);

        store.setState((state) => ({
            ...state,
            application: {
                ...state.application,
                apiAvailable: false,
            },
        }));

        setApiStatus("error");
        return false;
    }
}

function hasActiveFilters(filters) {
    return Object.values(filters).some((value) => (
        value !== null &&
        value !== undefined &&
        String(value).trim() &&
        String(value).toUpperCase() !== "ALL"
    ));
}

function loadDashboardCatalog() {
    if (dashboardCatalog) {
        return Promise.resolve(dashboardCatalog);
    }
    if (dashboardCatalogPromise) {
        return dashboardCatalogPromise;
    }

    setDashboardFilterCatalogState("loading");
    dashboardCatalogError = null;
    dashboardCatalogPromise = (async () => {
        try {
            const response = await apiClient.get("/dashboard", {
                query: EMPTY_DASHBOARD_FILTERS,
            });
            const data = validateDashboardPayload(response);

            if (!dashboardCatalog) {
                populateDashboardFilters(data);
                dashboardCatalog = data;
                setDashboardFilterCatalogState("ready");
            }

            return dashboardCatalog;
        } catch (error) {
            dashboardCatalogError = error;
            console.error("Dashboard filter catalog request failed:", error);
            setDashboardFilterCatalogState(
                "error",
                dashboardErrorMessage(error),
            );
            return null;
        } finally {
            dashboardCatalogPromise = null;
        }
    })();

    return dashboardCatalogPromise;
}

async function refreshDashboard(filters = store.getState().filters) {
    const requestId = ++latestDashboardRequest;
    const previousController = activeDashboardController;
    activeDashboardController = null;
    previousController?.abort();

    const currentData = store.getState().dashboard.data;
    const needsCatalog = !dashboardCatalog;
    const catalogPromise = loadDashboardCatalog();
    const useCatalogForResults =
        needsCatalog && !hasActiveFilters(filters);
    const requestController = useCatalogForResults
        ? null
        : new AbortController();
    if (requestController) {
        activeDashboardController = requestController;
    }

    store.setState((state) => ({
        ...state,
        dashboard: {
            ...state.dashboard,
            loading: true,
            error: null,
        },
    }));
    setDashboardLoading(true);

    const errorPanel = document.getElementById("dashboard-error");
    if (errorPanel) errorPanel.hidden = true;

    if (!currentData) {
        const results = document.getElementById("dashboard-results");
        if (results) results.hidden = true;
    }

    try {
        const response = useCatalogForResults
            ? await catalogPromise
            : await apiClient.get("/dashboard", {
                query: filters,
                signal: requestController.signal,
            });
        if (requestId !== latestDashboardRequest) return;
        if (!response) {
            throw dashboardCatalogError ?? new Error(
                "Le catalogue complet des filtres n’a pas pu être chargé.",
            );
        }

        const data = validateDashboardPayload(response);
        store.setState((state) => ({
            ...state,
            dashboard: {
                ...state.dashboard,
                loading: false,
                error: null,
                data,
            },
            application: {
                ...state.application,
                apiAvailable: true,
            },
        }));
        renderDashboard(data);
        setApiStatus("success");
    } catch (error) {
        if (error?.code === "REQUEST_CANCELLED") {
            if (requestId === latestDashboardRequest) {
                store.setState((state) => ({
                    ...state,
                    dashboard: {
                        ...state.dashboard,
                        loading: false,
                    },
                }));
                setDashboardLoading(false);
            }
            return;
        }
        if (requestId !== latestDashboardRequest) return;

        const message = dashboardErrorMessage(error);
        console.error("Dashboard request failed:", error);
        store.setState((state) => ({
            ...state,
            dashboard: {
                ...state.dashboard,
                loading: false,
                error: message,
            },
            application: {
                ...state.application,
                apiAvailable: error?.status === 422,
            },
        }));
        setApiStatus("error", {
            text: error?.status === 422 ? "Filtre invalide" : "Indisponible",
        });
        setDashboardLoading(false);
        const results = document.getElementById("dashboard-results");
        if (results) results.hidden = true;
        renderDashboardError(message);
        return;
    } finally {
        if (activeDashboardController === requestController) {
            activeDashboardController = null;
        }
    }

    setDashboardLoading(false);
}

function normalizeFilters(filters) {
    return Object.fromEntries(
        Object.entries(filters).map(([key, value]) => [
            key,
            typeof value === "string" && value.toUpperCase() === "ALL"
                ? null
                : value,
        ]),
    );
}

function updateDashboardFilters() {
    const filters = normalizeFilters(getDashboardFilterValues());

    store.setState((state) => ({
        ...state,
        filters: {
            ...state.filters,
            ...filters,
        },
    }));

    if (dashboardFilterDebounceTimer !== null) {
        window.clearTimeout(dashboardFilterDebounceTimer);
    }
    dashboardFilterDebounceTimer = window.setTimeout(() => {
        dashboardFilterDebounceTimer = null;
        const currentFilters = normalizeFilters(getDashboardFilterValues());
        store.setState((state) => ({
            ...state,
            filters: {
                ...state.filters,
                ...currentFilters,
            },
        }));
        refreshDashboard(store.getState().filters);
    }, DASHBOARD_FILTER_DEBOUNCE_MS);
}

function resetDashboardFilters() {
    cancelDashboardFilterDebounce();

    resetDashboardFilterInputs();
    const filters = {
        dateFrom: null,
        dateTo: null,
        client: null,
        problem: null,
        priority: null,
        technician: null,
    };

    store.setState((state) => ({
        ...state,
        filters,
    }));

    return refreshDashboard(filters);
}

function cancelDashboardFilterDebounce() {
    if (dashboardFilterDebounceTimer !== null) {
        window.clearTimeout(dashboardFilterDebounceTimer);
        dashboardFilterDebounceTimer = null;
    }
}

function refreshDashboardImmediately() {
    cancelDashboardFilterDebounce();
    const filters = normalizeFilters(getDashboardFilterValues());
    store.setState((state) => ({
        ...state,
        filters: {
            ...state.filters,
            ...filters,
        },
    }));
    return refreshDashboard(store.getState().filters);
}

function bindDashboardFilterEvents() {
    const filterIds = [
        "filter-date-from",
        "filter-date-to",
        "filter-client",
        "filter-problem",
        "filter-priority",
        "filter-technician",
    ];

    for (const id of filterIds) {
        const element = document.getElementById(id);
        element?.addEventListener("change", updateDashboardFilters);
    }

    document
        .getElementById("filters-reset")
        ?.addEventListener("click", resetDashboardFilters);
    document
        .getElementById("dashboard-retry")
        ?.addEventListener("click", refreshDashboardImmediately);
    document
        .getElementById("filter-catalog-retry")
        ?.addEventListener("click", refreshDashboardImmediately);
}

async function bootstrap() {
    bindDashboardFilterEvents();
    bindRegistryEvents();
    await checkApiHealth();

    try {
        await refreshDashboard();
    } finally {
        store.setState((state) => ({
            ...state,
            application: {
                ...state.application,
                initialized: true,
            },
        }));
        setApplicationReady(true);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    bootstrap();
});

export {
    bindDashboardFilterEvents,
    bootstrap,
    checkApiHealth,
    loadDashboardCatalog,
    refreshDashboard,
    resetDashboardFilters,
    updateDashboardFilters,
    validateDashboardPayload,
};
