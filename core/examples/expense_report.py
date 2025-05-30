import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import ListContent, TextContent
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code

from pipelex_libraries.pipelines.examples.expense_report.expense_report import ExpenseValidationCombo


def read_text_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


async def process_expense_report() -> ListContent[ExpenseValidationCombo]:
    invoice_dejeuner_1 = read_text_file("assets/expense_report/invoice_dejeuner_1.txt")
    invoice_dejeuner_2 = read_text_file("assets/expense_report/invoice_dejeuner_2.txt")
    invoice_diner = read_text_file("assets/expense_report/invoice_diner.txt")
    invoice_flight = read_text_file("assets/expense_report/invoice_flight.txt")
    invoice_hotel = read_text_file("assets/expense_report/invoice_hotel.txt")
    invoice_trajet = read_text_file("assets/expense_report/invoice_trajet.txt")
    expense_report_str = read_text_file("assets/expense_report/expense_report.txt")

    # Create Stuff objects
    invoice_list = StuffFactory.make_stuff(
        concept_code="expense_report.InvoiceText",
        content=ListContent(
            items=[
                TextContent(text=invoice_dejeuner_1),
                TextContent(text=invoice_dejeuner_2),
                TextContent(text=invoice_diner),
                TextContent(text=invoice_flight),
                TextContent(text=invoice_hotel),
                TextContent(text=invoice_trajet),
            ]
        ),
        name="invoice_text_list",
    )
    expense_report_text = StuffFactory.make_stuff(
        concept_code="expense_report.ExpenseReportText",
        content=TextContent(text=expense_report_str),
        name="expense_report_text",
    )

    # Create Working Memory
    working_memory = WorkingMemoryFactory.make_from_multiple_stuffs([invoice_list, expense_report_text])

    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="process_expense_report",
        working_memory=working_memory,
    )
    return pipe_output.main_stuff_as_list(item_type=ExpenseValidationCombo)


# start Pipelex
Pipelex.make()
# run sample using asyncio
expense_validations = asyncio.run(process_expense_report())

# Display cost report (tokens used and cost)
get_report_delegate().generate_report()
# output results
pretty_print(expense_validations, title="Expense validations")
