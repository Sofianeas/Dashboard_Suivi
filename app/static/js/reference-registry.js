"use strict";

import { apiClient } from "./core/api.js";

let lastSearch = null;
let selectedTicketId = null;

const CLASSIFICATION_LABELS = {
    B: "Partiellement documenté",
    C: "Ambigu",
    D: "Mention seule",
    not_applicable_existing_structured_record: "Déjà présent au dashboard",
};

const FIELD_LABELS = {
    ticket_date: "Date du ticket",
    client_analytic: "Client normalisé",
    problem_analytic: "Problématique normalisée",
    priority_analytic: "Priorité",
    opened_at: "Ouverture",
    resolved_at: "Résolution",
    resolution_minutes: "Durée SLA",
    technician_analytic: "Technicien assigné",
};

function element(id) {
    return document.getElementById(id);
}

function textElement(tagName, className, text) {
    const node = document.createElement(tagName);
    if (className) node.className = className;
    node.textContent = text ?? "";
    return node;
}

function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
}

function showSearchError(message) {
    element("registry-error-message").textContent = message;
    element("registry-error").hidden = false;
    element("registry-loading").hidden = true;
}

function showDetailError(message) {
    element("registry-detail-error-message").textContent = message;
    element("registry-detail-error").hidden = false;
    element("registry-detail-loading").hidden = true;
}

function readableError(error) {
    if (error?.message === "API request timed out.") {
        return "La requête a expiré. Réessayez.";
    }
    if (error?.status === 404) {
        return "Cet identifiant n’est plus disponible dans le registre.";
    }
    if (error?.status === 503) {
        return "Le registre est momentanément indisponible. Réessayez plus tard.";
    }
    if (error?.status) {
        return "La recherche n’a pas abouti. Réessayez.";
    }
    return "Impossible de joindre le service. Vérifiez la connexion puis réessayez.";
}

function classificationLabel(value) {
    return CLASSIFICATION_LABELS[value] ?? "Classification indisponible";
}

function renderSearchResults(payload) {
    const list = element("registry-result-list");
    clear(list);
    element("registry-results").hidden = false;
    element("registry-empty").hidden = payload.results.length > 0;
    element("registry-initial").hidden = true;
    const count = payload.total === 1
        ? "1 identifiant trouvé"
        : `${payload.total} identifiants trouvés`;
    element("registry-results-count").textContent = payload.truncated
        ? `${count} (premiers résultats affichés)`
        : count;

    for (const result of payload.results) {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "registry-result-button";
        button.dataset.ticketId = result.ticket_id;
        button.setAttribute(
            "aria-pressed",
            String(result.ticket_id === selectedTicketId),
        );
        const ticket = textElement(
            "span",
            "registry-result-button__ticket",
            result.ticket_id,
        );
        const meta = textElement(
            "span",
            "registry-result-button__meta",
            `${result.message_count} message(s) · ${classificationLabel(result.classification)}`,
        );
        button.append(ticket, meta);
        button.addEventListener("click", () => loadTicketDetails(result.ticket_id));
        item.append(button);
        list.append(item);
    }
}

function addSummaryItem(list, label, value) {
    const wrapper = document.createElement("div");
    wrapper.append(
        textElement("dt", "", label),
        textElement("dd", "", value || "Non renseigné"),
    );
    list.append(wrapper);
}

function renderTicketDetails(ticket) {
    const panel = element("registry-detail");
    clear(panel);
    panel.hidden = false;

    const header = document.createElement("header");
    header.className = "registry-detail__header";
    header.append(
        textElement("h2", "", ticket.ticket_id),
        textElement(
            "span",
            "registry-badge",
            classificationLabel(ticket.classification),
        ),
    );
    panel.append(header);

    const notice = textElement("p", "registry-detail__notice", ticket.notice);
    panel.append(notice);

    const summary = document.createElement("dl");
    summary.className = "registry-summary";
    addSummaryItem(summary, "Messages associés", String(ticket.message_count));
    addSummaryItem(
        summary,
        "Rapprochement analytique",
        ticket.reconciliation_status === "present_in_official_csv"
            ? "Identifiant déjà présent dans le dataset SLA"
            : "Identifiant absent du dataset SLA",
    );
    addSummaryItem(
        summary,
        "Champs non établis",
        ticket.missing_fields
            .map((field) => FIELD_LABELS[field] ?? field)
            .join(", "),
    );
    addSummaryItem(summary, "Ambiguïté", ticket.ambiguity);
    panel.append(summary);

    const messageList = document.createElement("div");
    messageList.className = "registry-message-list";
    for (const message of ticket.messages) {
        const card = document.createElement("article");
        card.className = "registry-message";
        const meta = document.createElement("div");
        meta.className = "registry-message__meta";
        for (const label of [
            `Message ${message.event_id}`,
            `Ligne source ${message.source_line}`,
            `Horodatage du message : ${message.timestamp || "indisponible"}`,
            `Expéditeur : ${message.sender || "non renseigné"}`,
        ]) {
            meta.append(textElement("span", "", label));
        }
        card.append(meta);
        if (message.title) {
            card.append(textElement("h3", "", message.title));
        }
        if (message.body) {
            card.append(textElement("p", "registry-message__body", message.body));
        }
        if (message.multiple_ticket_ids) {
            card.append(textElement(
                "p",
                "registry-message__warning",
                `Message commun à plusieurs identifiants : ${message.linked_ticket_ids}. Le texte n’est pas attribué exclusivement à ce ticket.`,
            ));
        }
        const unverified = [];
        if (message.duration_text_unverified) {
            unverified.push(
                `Durée textuelle non vérifiée : ${message.duration_text_unverified}`,
            );
        }
        if (message.status_text_unverified) {
            unverified.push(
                `Statut textuel non vérifié : ${message.status_text_unverified}`,
            );
        }
        if (unverified.length) {
            card.append(textElement(
                "p",
                "registry-message__warning",
                unverified.join(" · "),
            ));
        }
        messageList.append(card);
    }
    if (ticket.messages.length === 0) {
        messageList.append(textElement(
            "p",
            "registry-empty",
            "Aucun message associé n’est disponible pour cet identifiant.",
        ));
    }
    panel.append(messageList);
}

async function searchTickets(query, exact) {
    lastSearch = { query, exact };
    selectedTicketId = null;
    element("registry-detail").hidden = true;
    element("registry-detail-error").hidden = true;
    element("registry-results").hidden = true;
    element("registry-error").hidden = true;
    element("registry-loading").hidden = false;

    try {
        const payload = await apiClient.get(
            `/reference-registry?q=${encodeURIComponent(query)}&exact=${exact}`,
        );
        if (
            !payload ||
            !Array.isArray(payload.results) ||
            !Number.isFinite(payload.total)
        ) {
            throw new Error("Réponse invalide.");
        }
        renderSearchResults(payload);
        element("registry-error").hidden = true;
    } catch (error) {
        console.error("Secondary ticket reference search failed:", error);
        showSearchError(readableError(error));
    } finally {
        element("registry-loading").hidden = true;
    }
}

async function loadTicketDetails(ticketId) {
    selectedTicketId = ticketId;
    element("registry-detail-error").hidden = true;
    element("registry-detail").hidden = true;
    element("registry-detail-loading").hidden = false;
    for (const button of element("registry-result-list").querySelectorAll(
        ".registry-result-button",
    )) {
        button.setAttribute(
            "aria-pressed",
            String(button.dataset.ticketId === ticketId),
        );
    }

    try {
        const ticket = await apiClient.get(
            `/reference-registry/${encodeURIComponent(ticketId)}`,
        );
        if (!ticket || ticket.ticket_id !== ticketId || !Array.isArray(ticket.messages)) {
            throw new Error("Réponse invalide.");
        }
        renderTicketDetails(ticket);
    } catch (error) {
        console.error("Secondary ticket reference details failed:", error);
        showDetailError(readableError(error));
    } finally {
        element("registry-detail-loading").hidden = true;
    }
}

function bindRegistryEvents() {
    element("registry-search-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        const query = element("registry-query").value.trim();
        if (!query) return;
        searchTickets(
            query,
            element("registry-search-mode").value === "exact",
        );
    });

    element("registry-retry")?.addEventListener("click", () => {
        if (lastSearch) searchTickets(lastSearch.query, lastSearch.exact);
    });

    element("registry-detail-retry")?.addEventListener("click", () => {
        if (selectedTicketId) loadTicketDetails(selectedTicketId);
    });

    const viewTargets = document.querySelectorAll("[data-app-view]");
    for (const target of viewTargets) {
        target.addEventListener("click", (event) => {
            if (target.dataset.appView === "dashboard") {
                event.preventDefault();
            }
            const registryVisible =
                target.dataset.appView === "reference-registry";
            element("dashboard-view").hidden = registryVisible;
            element("reference-registry-view").hidden = !registryVisible;
            for (const navItem of viewTargets) {
                const active = navItem === target;
                navItem.classList.toggle("navigation-item--active", active);
                navItem.setAttribute("aria-current", active ? "page" : "false");
            }
            if (registryVisible) element("registry-query").focus();
        });
    }
}

export { bindRegistryEvents, loadTicketDetails, renderSearchResults, searchTickets };
