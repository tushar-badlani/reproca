from pathlib import Path

from reproca.app import App
from reproca.code_generation import CodeGenerator
from reproca.method import methods
from reproca.sessions import Sessions

from .models import Session

sessions: Sessions[int, Session] = Sessions()

from . import todo

__all__ = ["todo"]

with Path("src/frontend/api.ts").open("w") as file:
    code_generator = CodeGenerator(file)
    code_generator.write(
        """
        import {type MethodResult, App} from "reproca/app"
        import {circuitBreakerMiddleware} from "~/query"
        const app = new App(import.meta.env.VITE_API, circuitBreakerMiddleware({
            maxFailures: 3,
            resetTimeout: 15000
        }))
        """
    )
    for method in methods.values():
        code_generator.method(method)
    code_generator.resolve()

app = App(sessions)


def dry() -> None:
    pass
