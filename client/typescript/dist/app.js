export class ProtocolError extends Error {
}
export class App {
    host;
    middleware;
    constructor(host, middleware) {
        this.host = host;
        this.middleware = middleware;
    }
    async method(name, parameters) {
        const result = () => this._method(name, parameters);
        if (this.middleware) {
            return this.middleware(result);
        }
        return result();
    }
    async _method(name, parameters) {
        try {
            let result = await fetch(`${this.host}/${name}`, {
                method: "POST",
                headers: { "Content-Type": "text/plain" }, // simple request
                body: JSON.stringify(parameters),
                credentials: "include",
            });
            if (result.ok) {
                return { ok: true, value: await result.json() };
            }
            const body = await result.text();
            throw new ProtocolError(`Server returned ${result.statusText}${body && ` (${body})`} while calling method \`${name}\``);
        }
        catch (err) {
            if (err instanceof Error) {
                return { ok: false, value: err };
            }
            throw err;
        }
    }
}
