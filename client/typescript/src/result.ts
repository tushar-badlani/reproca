/* export interface Ok<T> {
    ok: true
    value: T
}

export interface Err<E> {
    ok: false
    value: E
}

export type Result<T, E> = Ok<T> | Err<E> */

type Ok<T> = { ok: T };
type Err<T> = { err: T };
type Result<T, E> = Ok<T> | Err<E>;

const foo: Result<number, string> = {
  ok: 123,
  err: "error",
};
