import {App, type MethodResult} from "reproca/app"
import {circuitBreakerMiddleware} from "~/query"
const app = new App(
    import.meta.env.VITE_API,
    circuitBreakerMiddleware({
        maxFailures: 3,
        resetTimeout: 15000
    })
)
/**
 * Create a new todo item with the given title and description.
 *
 *Args:
 *----
 *title: The title of the todo item.
 *description: The description of the todo item.
 *
 *Returns:
 *-------
 *The ID of the newly created todo item.
 *
 */
export async function create_todo(
    parameters: CreateTodoParameters
): Promise<MethodResult<string>> {
    return await app.method("create_todo", parameters)
}
export async function get_todos(
    parameters: GetTodosParameters = {}
): Promise<MethodResult<Todo[]>> {
    return await app.method("get_todos", parameters)
}
export async function update_todo(
    parameters: UpdateTodoParameters
): Promise<MethodResult<null>> {
    return await app.method("update_todo", parameters)
}
export async function delete_todo(
    parameters: DeleteTodoParameters
): Promise<MethodResult<null>> {
    return await app.method("delete_todo", parameters)
}
export interface CreateTodoParameters {
    title: string
    description: string
}
export interface GetTodosParameters {}
export interface UpdateTodoParameters {
    todo_id: string
    title?: string
    description?: string
    done?: boolean
}
export interface Todo {
    title: string
    description: string
    done: boolean
    id: string
}
export interface DeleteTodoParameters {
    todo_id: string
}
