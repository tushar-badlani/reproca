import {useComputed, useSignal} from "@preact/signals-react"
import type {ComponentProps} from "react"
import * as api from "./api"
import {useMutation, useQuery, type QuerySignal} from "./query"

interface InputProps extends ComponentProps<"input"> {
    label: string
}

function Input({label, className, ...props}: InputProps) {
    return (
        <div className={`input ${className}`}>
            <p className="input__label">{label}</p>
            <input className="input__inner" {...props} />
        </div>
    )
}

function Todo({
    todo,
    updateTodo,
    deleteTodo
}: {
    todo: api.Todo
    updateTodo: typeof api.update_todo
    deleteTodo: typeof api.delete_todo
}) {
    function onDelete() {
        void deleteTodo({todo_id: todo.id})
    }
    function onUpdateDone() {
        void updateTodo({todo_id: todo.id, done: !todo.done})
    }
    return (
        <div className="todo">
            <input
                className="todo__done"
                type="checkbox"
                checked={todo.done}
                onChange={onUpdateDone}
            />
            <div className="todo__details">
                <p className="todo__title">{todo.title}</p>
                <p className="todo__description">{todo.description}</p>
            </div>
            <button className="todo__delete button" onClick={onDelete}>
                DELETE
            </button>
        </div>
    )
}

function TodoInput({createTodo}: {createTodo: typeof api.create_todo}) {
    const title = useSignal("")
    const description = useSignal("")
    const lines = useComputed(() => `${description.value.split("\n").length}lh`)
    function onCreate() {
        void createTodo({
            title: title.value,
            description: description.value
        })
    }
    return (
        <div className="todo-input">
            <Input
                className="todo-input__title"
                label="Title"
                type="text"
                value={title.value}
                onInput={(event) => {
                    title.value = (event.target as HTMLInputElement).value
                }}
            />
            <textarea
                className="textarea todo-input__description"
                style={{["--lines" as string]: lines.value}}
                value={description.value}
                onInput={(event) => {
                    description.value = (event.target as HTMLTextAreaElement).value
                }}
            />
            <button className="todo-input__create button" onClick={onCreate}>
                CREATE
            </button>
        </div>
    )
}

function TodoList({
    todos,
    updateTodo,
    deleteTodo
}: {
    todos: QuerySignal<api.Todo[]>
    updateTodo: typeof api.update_todo
    deleteTodo: typeof api.delete_todo
}) {
    return (
        <div className="todo-list">
            {todos.ok ?
                todos.value.map((todo) => (
                    <Todo
                        key={todo.id}
                        todo={todo}
                        updateTodo={updateTodo}
                        deleteTodo={deleteTodo}
                    />
                ))
            :   <div className="spinner" />}
        </div>
    )
}

export function App() {
    const [todos, fetchTodos] = useQuery(api.get_todos, {keepPrevious: true})
    const createTodo = useMutation(todos, fetchTodos, api.create_todo)
    const updateTodo = useMutation(todos, fetchTodos, api.update_todo, {
        update: (todos, {todo_id, title, description, done}) => {
            const index = todos.findIndex((todo) => todo.id === todo_id)
            if (title !== undefined) {
                todos[index].title = title
            }
            if (description !== undefined) {
                todos[index].description = description
            }
            if (done !== undefined) {
                todos[index].done = done
            }
        }
    })
    const deleteTodo = useMutation(todos, fetchTodos, api.delete_todo, {
        update: (todos, {todo_id}) => {
            const index = todos.findIndex((todo) => todo.id === todo_id)
            todos.splice(index, 1)
        }
    })
    return (
        <div className="app">
            <TodoInput createTodo={createTodo} />
            <TodoList todos={todos} updateTodo={updateTodo} deleteTodo={deleteTodo} />
        </div>
    )
}
