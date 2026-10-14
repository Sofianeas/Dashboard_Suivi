"use strict";

const initialState = Object.freeze({
    application: {
        initialized: false,
        apiAvailable: null,
    },
    dashboard: {
        loading: false,
        error: null,
        data: null,
    },
    filters: {
        dateFrom: null,
        dateTo: null,
        client: null,
        problem: null,
        priority: null,
        technician: null,
    },
});

function clone(value) {
    return structuredClone(value);
}

export class Store {
    #state;
    #listeners;

    constructor(state = initialState) {
        this.#state = clone(state);
        this.#listeners = new Set();
    }

    getState() {
        return clone(this.#state);
    }

    setState(updater) {
        const currentState = this.getState();
        const nextState =
            typeof updater === "function"
                ? updater(currentState)
                : updater;

        if (nextState === null || typeof nextState !== "object") {
            throw new TypeError(
                "Store.setState() expects an object or updater function."
            );
        }

        this.#state = {
            ...currentState,
            ...nextState,
        };

        this.#notify();
    }

    subscribe(listener) {
        if (typeof listener !== "function") {
            throw new TypeError("Store.subscribe() expects a function.");
        }

        this.#listeners.add(listener);

        return () => {
            this.#listeners.delete(listener);
        };
    }

    #notify() {
        const snapshot = this.getState();

        for (const listener of this.#listeners) {
            listener(snapshot);
        }
    }
}

export const store = new Store();
