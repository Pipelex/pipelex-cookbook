from pipelex.cogt.model_backends.backend import InferenceBackend
from pipelex.hub import get_console
from rich import box
from rich.table import Table


def list_hello_models(
    *,
    sdk: str,
    backend_name: str,
    backend: InferenceBackend,
    flat: bool,
    any_listed: bool,
) -> None:
    """List the models the hello backend declares in its config.

    There is no remote API to enumerate, so the lister simply reads the model
    specs declared in `.pipelex/inference/backends/hello.toml`.
    """
    console = get_console()
    model_names = backend.list_model_names()

    if flat:
        if not any_listed:
            console.print("model_id,sdk,backend")
        for model_name in model_names:
            model_spec = backend.get_model_spec(model_name)
            model_id = model_spec.model_id if model_spec else model_name
            console.print(f"{model_id},{sdk},{backend_name}")
        return

    table = Table(
        title=f"Available Models for Backend '{backend_name}' (SDK: {sdk})",
        show_header=True,
        header_style="bold cyan",
        box=box.SQUARE_DOUBLE_HEAD,
    )
    table.add_column("Model ID", style="green")
    table.add_column("Model Type", style="blue")

    for model_name in model_names:
        model_spec = backend.get_model_spec(model_name)
        if model_spec is None:
            continue
        table.add_row(model_spec.model_id, model_spec.model_type)

    console.print("\n")
    console.print(table)
    console.print("\n")
