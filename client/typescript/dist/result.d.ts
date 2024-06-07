export interface Ok<T> {
    ok: true;
    value: T;
}
export interface Err<E> {
    ok: false;
    value: E;
}
export type Result<T, E> = Ok<T> | Err<E>;
