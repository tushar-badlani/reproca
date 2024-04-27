import {StrictMode} from "react"
import {createRoot} from "react-dom/client"
import {App} from "~/App"
import "~/reset.css"
import "~/style.css"

const main = document.getElementById("main") as HTMLDivElement
const root = createRoot(main)
root.render(
    <StrictMode>
        <App />
    </StrictMode>
)
