import type { Result } from "./result";
export type MethodResult<T> = Result<T, Error>;
export declare class ProtocolError extends Error {
}
export type Middleware = <T>(result: () => Promise<MethodResult<T>>) => Promise<MethodResult<T>>;
export declare class App<M> {
    host: string;
    middleware?: Middleware | undefined;
    constructor(host: string, middleware?: Middleware | undefined);
    method<T, R>(name: string, parameters: T): Promise<MethodResult<R>>;
    _method<T, R>(name: string, parameters: T): Promise<MethodResult<R>>;
}
