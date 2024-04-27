import {batch, signal, useSignalEffect} from "@preact/signals-react"
import type {DeepSignal} from "deepsignal"
import {deepSignal, useDeepSignal} from "deepsignal/react"
import type {MethodResult} from "reproca/app"

export enum QueryType {
    OK = "OK",
    STALE = "STALE",
    LOADING = "LOADING",
    ERROR = "ERROR"
}

export type QueryResult<T> =
    | {
          type: QueryType.ERROR
          value: T
      }
    | {
          type: QueryType.LOADING
          value: undefined
      }
    | {
          type: QueryType.OK
          value: T
      }
    | {
          type: QueryType.STALE
          value: T
      }

export function useQuery<T extends object>(method: () => Promise<MethodResult<T>>) {
    const signal = useDeepSignal<QueryResult<T>>({
        type: QueryType.LOADING,
        value: undefined
    })

    async function fetch() {
        const result = await method()
        signal.type = QueryType.STALE
        if (!result.ok) {
            signal.type = QueryType.ERROR
            return
        }
        batch(() => {
            signal.type = QueryType.OK
            if (signal.value === undefined) {
                signal.value = deepSignal(result.value)
                return
            }
            Object.assign(signal.value, result.value)
        })
    }

    useSignalEffect(() => {
        void fetch()
    })

    return [signal, fetch] as const
}

export type QuerySignal<T extends object> = ReturnType<typeof useQuery<T>>[0]

export interface UseMutationOptions<T extends object, P extends object> {
    update?: (signal: DeepSignal<T>, parameters: P) => void
}

export function useMutation<T extends object, P extends object, R>(
    signal: QuerySignal<T>,
    fetch: () => Promise<void>,
    method: (parameters: P) => Promise<MethodResult<R>>,
    options: UseMutationOptions<T, P> = {}
) {
    async function mutate(parameters: P): Promise<MethodResult<R>> {
        if (options.update) {
            if (signal.value !== undefined) {
                batch(() => {
                    // eslint-disable-next-line @typescript-eslint/prefer-ts-expect-error, @typescript-eslint/ban-ts-comment
                    // @ts-ignore
                    options.update(signal.value, parameters)
                })
            }
        }
        const result = await method(parameters)
        if (result.ok) {
            void fetch()
        }
        return result
    }
    return mutate
}

export enum CircuitBreakerState {
    CLOSED = "CLOSED",
    OPEN = "OPEN",
    HALF_OPEN = "HALF_OPEN"
}

export interface CircuitBreakerOptions {
    maxFailures?: number
    resetTimeout?: number
}

export function circuitBreakerMiddleware({
    maxFailures = 3,
    resetTimeout = 15000
}: CircuitBreakerOptions = {}) {
    const state = signal(CircuitBreakerState.CLOSED)
    let failures = 0
    let timeout: number | undefined
    async function middleware<T>(
        method: () => Promise<MethodResult<T>>
    ): Promise<MethodResult<T>> {
        let result
        switch (state.value) {
            case CircuitBreakerState.CLOSED:
                result = await method()
                if (result.ok) {
                    failures = 0
                } else {
                    failures += 1
                    if (failures >= maxFailures) {
                        clearTimeout(timeout)
                        state.value = CircuitBreakerState.OPEN
                        timeout = window.setTimeout(() => {
                            state.value = CircuitBreakerState.HALF_OPEN
                        }, resetTimeout)
                    }
                }
                return result
            case CircuitBreakerState.OPEN:
                return {ok: false, value: new Error("Circuit breaker open")}
            case CircuitBreakerState.HALF_OPEN:
                result = await method()
                if (result.ok) {
                    state.value = CircuitBreakerState.CLOSED
                } else {
                    clearTimeout(timeout)
                    state.value = CircuitBreakerState.OPEN
                    timeout = window.setTimeout(() => {
                        state.value = CircuitBreakerState.HALF_OPEN
                    }, resetTimeout)
                }
                return result
        }
    }
    return middleware
}
