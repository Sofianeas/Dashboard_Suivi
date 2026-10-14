"use strict";

const numberFormat = new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: 1,
});

const dateFormat = new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
});

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

export function setApiStatus(status, { text = null } = {}) {
    const element = document.getElementById("api-status");
    const header = document.querySelector(".header-status");
    if (!element) return;

    const classes = [
        "status--loading",
        "status--success",
        "status--error",
    ];

    element.classList.remove(...classes);

    switch (status) {
        case "success":
            element.classList.add("status--success");
            element.textContent = text ?? "Connectée";
            break;
        case "error":
            element.classList.add("status--error");
            element.textContent = text ?? "Indisponible";
            break;
        default:
            element.classList.add("status--loading");
            element.textContent = text ?? "Connexion…";
            break;
    }

    header?.setAttribute("data-status", status);
}

export function setApplicationReady(isReady) {
    document.documentElement.dataset.appReady = String(Boolean(isReady));
}

export function formatInteger(value) {
    const number = Number(value);
    if (value === null || value === undefined || !Number.isFinite(number)) {
        return "—";
    }
    return new Intl.NumberFormat("fr-FR", {
        maximumFractionDigits: 0,
    }).format(number);
}

export function formatMinutes(value) {
    const minutes = Number(value);
    if (value === null || value === undefined || !Number.isFinite(minutes)) {
        return "—";
    }

    if (minutes < 60) {
        return `${numberFormat.format(minutes)} min`;
    }

    const roundedTenths = Math.round(minutes * 10);
    const hours = Math.floor(roundedTenths / 600);
    const remainingMinutes = (roundedTenths % 600) / 10;
    return `${hours} h ${numberFormat.format(remainingMinutes)} min`;
}

export function getDashboardFilterValues() {
    return {
        dateFrom: document.getElementById("filter-date-from")?.value || null,
        dateTo: document.getElementById("filter-date-to")?.value || null,
        client: document.getElementById("filter-client")?.value || null,
        problem: document.getElementById("filter-problem")?.value || null,
        priority: document.getElementById("filter-priority")?.value || null,
        technician: document.getElementById("filter-technician")?.value || null,
    };
}

export function resetDashboardFilterInputs() {
    const dateFrom = document.getElementById("filter-date-from");
    const dateTo = document.getElementById("filter-date-to");

    if (dateFrom) dateFrom.value = "";
    if (dateTo) dateTo.value = "";

    for (const id of [
        "filter-client",
        "filter-problem",
        "filter-priority",
        "filter-technician",
    ]) {
        const element = document.getElementById(id);
        if (element) element.value = "ALL";
    }
}

export function populateDashboardFilters(data) {
    const dimensions = [
        { id: "filter-client", key: "clients", field: "client" },
        { id: "filter-problem", key: "problems", field: "problem" },
        { id: "filter-priority", key: "priorities", field: "priority" },
        { id: "filter-technician", key: "technicians", field: "technician" },
    ];

    for (const dimension of dimensions) {
        const select = document.getElementById(dimension.id);
        if (!select) continue;

        const selectedValue = select.value;
        while (select.options.length > 1) {
            select.remove(1);
        }

        const values = data[dimension.key]
            .map((row) => row[dimension.field])
            .filter((value) => typeof value === "string" && value.trim())
            .sort((left, right) => left.localeCompare(right, "fr"));

        for (const value of values) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            select.append(option);
        }

        if (values.includes(selectedValue)) {
            select.value = selectedValue;
        } else {
            select.value = "ALL";
        }
    }
}

export function setDashboardFilterCatalogState(status, message = "") {
    const statusElement = document.getElementById("filter-catalog-status");
    const retryButton = document.getElementById("filter-catalog-retry");
    const selects = [
        "filter-client",
        "filter-problem",
        "filter-priority",
        "filter-technician",
    ];

    for (const id of selects) {
        const select = document.getElementById(id);
        if (select) select.disabled = status !== "ready";
    }

    if (statusElement) {
        statusElement.hidden = status === "ready";
        statusElement.textContent = status === "loading"
            ? "Chargement des options de filtres…"
            : status === "error"
                ? `Options de filtres indisponibles. ${message}`
                : "";
    }
    if (retryButton) {
        retryButton.hidden = status !== "error";
        retryButton.disabled = status === "loading";
    }
}

export function setDashboardLoading(isLoading) {
    const loading = document.getElementById("dashboard-loading");
    const results = document.getElementById("dashboard-results");
    if (loading) loading.hidden = !isLoading;
    if (results) results.setAttribute("aria-busy", String(Boolean(isLoading)));
}

export function renderDashboardError(message) {
    const container = document.getElementById("dashboard-error");
    const messageElement = document.getElementById("dashboard-error-message");
    if (messageElement) messageElement.textContent = message;
    if (container) container.hidden = false;
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function renderDimensionChart(containerId, rows, fieldName) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.replaceChildren();

    const normalizedRows = rows
        .map((row) => ({
            label: String(row[fieldName] ?? ""),
            count: Number(row.ticket_count),
        }))
        .filter((row) => row.label && Number.isFinite(row.count))
        .sort((left, right) => (
            right.count - left.count ||
            left.label.localeCompare(right.label, "fr")
        ));

    if (!normalizedRows.length) {
        container.append(createEmptyMessage("Aucune donnée pour cette sélection."));
        return;
    }

    const maximum = Math.max(...normalizedRows.map((row) => row.count), 0);
    const list = document.createElement("div");
    list.className = "chart-list";
    list.setAttribute("role", "list");

    for (const row of normalizedRows) {
        const item = document.createElement("div");
        item.className = "chart-row";
        item.setAttribute("role", "listitem");
        item.title = `${row.label} : ${formatInteger(row.count)} ticket(s)`;

        const label = document.createElement("span");
        label.className = "chart-row__label";
        label.textContent = row.label;

        const track = document.createElement("span");
        track.className = "chart-row__track";
        track.setAttribute("aria-hidden", "true");

        const bar = document.createElement("span");
        bar.className = "chart-row__bar";
        bar.style.width = `${maximum > 0 ? (row.count / maximum) * 100 : 0}%`;
        track.append(bar);

        const count = document.createElement("span");
        count.className = "chart-row__value";
        count.textContent = formatInteger(row.count);

        item.append(label, track, count);
        list.append(item);
    }

    container.append(list);
}

function svgElement(name, attributes = {}) {
    const element = document.createElementNS(SVG_NAMESPACE, name);
    for (const [key, value] of Object.entries(attributes)) {
        element.setAttribute(key, String(value));
    }
    return element;
}

function createEmptyMessage(text) {
    const message = document.createElement("p");
    message.className = "chart-empty";
    message.textContent = text;
    return message;
}

function renderTemporalChart(rows) {
    const container = document.getElementById("chart-temporal");
    if (!container) return;
    container.replaceChildren();

    const points = rows
        .map((row) => ({
            period: String(row.period ?? ""),
            count: Number(row.ticket_count),
            mean: row.mean_resolution_minutes === null
                ? null
                : Number(row.mean_resolution_minutes),
        }))
        .filter((row) => (
            /^\d{4}-\d{2}-\d{2}$/.test(row.period) &&
            row.mean !== null &&
            Number.isFinite(row.mean) &&
            Number.isFinite(row.count)
        ))
        .sort((left, right) => left.period.localeCompare(right.period));

    if (!points.length) {
        container.append(createEmptyMessage("Aucune donnée temporelle pour cette sélection."));
        return;
    }

    const width = 820;
    const height = 290;
    const margins = { top: 20, right: 24, bottom: 52, left: 64 };
    const plotWidth = width - margins.left - margins.right;
    const plotHeight = height - margins.top - margins.bottom;
    const maximum = Math.max(...points.map((point) => point.mean), 1);
    const svg = svgElement("svg", {
        class: "temporal-chart",
        viewBox: `0 0 ${width} ${height}`,
        role: "img",
        "aria-label": "Durée moyenne de résolution en minutes par date de ticket",
        preserveAspectRatio: "xMidYMid meet",
    });

    const title = svgElement("title");
    title.textContent = "Durée moyenne de résolution par date de ticket";
    svg.append(title);

    for (let tick = 0; tick <= 4; tick += 1) {
        const ratio = tick / 4;
        const y = margins.top + plotHeight * ratio;
        const value = maximum * (1 - ratio);
        const gridLine = svgElement("line", {
            x1: margins.left,
            x2: width - margins.right,
            y1: y,
            y2: y,
            class: "temporal-grid-line",
        });
        const label = svgElement("text", {
            x: margins.left - 10,
            y: y + 4,
            "text-anchor": "end",
        });
        label.textContent = numberFormat.format(value);
        svg.append(gridLine, label);
    }

    const coordinates = points.map((point, index) => ({
        x: points.length === 1
            ? margins.left + plotWidth / 2
            : margins.left + (plotWidth * index) / (points.length - 1),
        y: margins.top + plotHeight * (1 - point.mean / maximum),
        point,
    }));

    const path = svgElement("polyline", {
        class: "temporal-series",
        points: coordinates.map(({ x, y }) => `${x},${y}`).join(" "),
    });
    svg.append(path);

    for (const { x, y, point } of coordinates) {
        const circle = svgElement("circle", {
            class: "temporal-point",
            cx: x,
            cy: y,
            r: points.length > 50 ? 2.6 : 4,
        });
        const tooltip = svgElement("title");
        tooltip.textContent = (
            `${point.period} : ${numberFormat.format(point.mean)} min de moyenne, ` +
            `${formatInteger(point.count)} ticket(s)`
        );
        circle.append(tooltip);
        svg.append(circle);
    }

    const labelCount = Math.min(points.length, 7);
    const labelIndexes = new Set(
        Array.from({ length: labelCount }, (_, index) => (
            labelCount === 1
                ? 0
                : Math.round((index * (points.length - 1)) / (labelCount - 1))
        ))
    );

    for (const index of labelIndexes) {
        const { x, point } = coordinates[index];
        const label = svgElement("text", {
            x,
            y: height - 19,
            "text-anchor": "middle",
        });
        const parsedDate = new Date(`${point.period}T12:00:00`);
        label.textContent = Number.isNaN(parsedDate.getTime())
            ? point.period
            : dateFormat.format(parsedDate);
        svg.append(label);
    }

    container.append(svg);
}

export function renderDashboard(data) {
    setText("kpi-ticket-count", formatInteger(data.kpi.ticket_count));
    setText(
        "kpi-resolution-mean",
        formatMinutes(data.kpi.mean_resolution_minutes),
    );
    setText(
        "kpi-resolution-median",
        formatMinutes(data.kpi.median_resolution_minutes),
    );

    renderTemporalChart(data.temporal);
    renderDimensionChart("chart-clients", data.clients, "client");
    renderDimensionChart("chart-problems", data.problems, "problem");
    renderDimensionChart("chart-priorities", data.priorities, "priority");
    renderDimensionChart("chart-technicians", data.technicians, "technician");

    const results = document.getElementById("dashboard-results");
    const error = document.getElementById("dashboard-error");
    if (results) results.hidden = false;
    if (error) error.hidden = true;
}
