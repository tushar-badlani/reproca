import type {Result} from "./result"

export type MethodResult<T> = Result<T, Error>

export class ProtocolError extends Error {}

export type Middleware = <T>(
    result: () => Promise<MethodResult<T>>
) => Promise<MethodResult<T>>

export class App<M> {
    constructor(public host: string, public middleware?: Middleware) {}

    async method<T, R>(name: string, parameters: T): Promise<MethodResult<R>> {
        const result = () => this._method<T, R>(name, parameters)
        if (this.middleware) {
            return this.middleware(result)
        }
        return result()
    }

    async _method<T, R>(name: string, parameters: T): Promise<MethodResult<R>> {
        try {
            let result = await fetch(`${this.host}/${name}`, {
                method: "POST",
                headers: {"Content-Type": "text/plain"}, // simple request
                body: JSON.stringify(parameters),
                credentials: "include",
            })
            if (result.ok) {
                return {ok: true, value: await result.json()}
            }
            const body = await result.text()
            throw new ProtocolError(
                `Server returned ${result.statusText}${
                    body && ` (${body})`
                } while calling method \`${name}\``
            )
        } catch (err) {
            if (err instanceof Error) {
                return {ok: false, value: err}
            }
            throw err
        }
    }
}
