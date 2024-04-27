import {batch, signal, useSignalEffect} from "@preact/signals-react"
import {useDeepSignal, type DeepSignal} from "deepsignal/react"
import type {MethodResult} from "reproca/app"
import type {Result} from "reproca/result"

export enum QueryError {
    INDETERMINATE,
    NETWORK_ERROR
}

export type QueryResult<T> = Result<T, QueryError>

export type QuerySignal<T> = DeepSignal<QueryResult<T>>

export interface QueryOptions1 {
    keepPrevious?: boolean
}

export interface QueryOptions2<T, U> {
    then: (result: T) => U
    keepPrevious?: boolean
}

export function useQuery<T, U>(
    query: () => Promise<MethodResult<T>>,
    options: QueryOptions2<T, U>
): readonly [signal: DeepSignal<QueryResult<U>>, fetch: () => Promise<void>]
export function useQuery<T>(
    query: () => Promise<MethodResult<T>>,
    options?: QueryOptions1
): readonly [signal: DeepSignal<QueryResult<T>>, fetch: () => Promise<void>]
export function useQuery<T, U>(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    query: any,
    options: QueryOptions1 | QueryOptions2<T, U> = {keepPrevious: false}
) {
    const signal = useDeepSignal<QueryResult<T>>({
        ok: false,
        value: QueryError.INDETERMINATE
    })
    async function fetch() {
        if (!options.keepPrevious) {
            batch(() => {
                signal.ok = false
                signal.value = QueryError.INDETERMINATE
            })
        }
        const result = await query()
        if (!result.ok) {
            batch(() => {
                signal.ok = false
                signal.value = QueryError.NETWORK_ERROR
            })
            return
        }
        batch(() => {
            signal.ok = true
            signal.value = "then" in options ? options.then(result.value) : result.value
        })
    }
    useSignalEffect(() => {
        void fetch()
    })
    return [signal, fetch] as const
}

export function useMutation<T, A, R>(
    signal: DeepSignal<QueryResult<T>>,
    fetch: () => Promise<void>,
    mutateFn: (args: A) => Promise<MethodResult<R>>,
    options: {
        update?: (signal: DeepSignal<T>, args: A) => void
    } = {}
) {
    async function mutate(args: A): Promise<MethodResult<R>> {
        const oldState = signal.value
        if (options.update) {
            if (signal.ok) {
                batch(() => {
                    signal.ok = true
                    options.update!(signal.value, args)
                })
            }
        }
        const result = await mutateFn(args)
        if (result.ok) {
            await fetch()
        } else {
            signal.value = oldState
        }
        return result
    }
    return mutate
}

enum CircuitBreaker {
    CLOSED,
    OPEN,
    HALF_OPEN
}

export function circuitBreakerMiddleware(options: {
    maxFailures: number
    resetTimeout: number
}) {
    const state = signal(CircuitBreaker.CLOSED)
    let failures = 0
    let timeout: number | undefined
    async function middleware<T>(
        method: () => Promise<MethodResult<T>>
    ): Promise<MethodResult<T>> {
        let result
        switch (state.value) {
            case CircuitBreaker.CLOSED:
                result = await method()
                if (!result.ok) {
                    failures++
                    if (failures >= options.maxFailures) {
                        state.value = CircuitBreaker.OPEN
                        window.clearTimeout(timeout)
                        timeout = window.setTimeout(() => {
                            state.value = CircuitBreaker.HALF_OPEN
                        }, options.resetTimeout)
                    }
                } else {
                    failures = 0
                }
                return result
            case CircuitBreaker.OPEN:
                return {ok: false, value: new Error("Circuit breaker open")}
            case CircuitBreaker.HALF_OPEN:
                result = await method()
                if (!result.ok) {
                    state.value = CircuitBreaker.OPEN
                    window.clearTimeout(timeout)
                    timeout = window.setTimeout(() => {
                        state.value = CircuitBreaker.HALF_OPEN
                    }, options.resetTimeout)
                } else {
                    state.value = CircuitBreaker.CLOSED
                }
                return result
        }
    }
    return middleware
}
