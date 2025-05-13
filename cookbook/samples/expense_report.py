# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Elastic-2.0
# "Pipelex" is a trademark of Evotis S.A.S.

import asyncio

from pipelex import pretty_print
from pipelex.core.stuff_content import ListContent, TextContent
from pipelex.core.stuff_factory import StuffFactory
from pipelex.core.working_memory_factory import WorkingMemoryFactory
from pipelex.hub import get_report_delegate
from pipelex.pipelex import Pipelex
from pipelex.run import run_pipe_code


def read_text_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


async def process_expense_report():
    invoice_dejeuner_1 = read_text_file("data/expense_report/invoice_dejeuner_1.txt")
    invoice_dejeuner_2 = read_text_file("data/expense_report/invoice_dejeuner_2.txt")
    invoice_diner = read_text_file("data/expense_report/invoice_diner.txt")
    invoice_flight = read_text_file("data/expense_report/invoice_flight.txt")
    invoice_hotel = read_text_file("data/expense_report/invoice_hotel.txt")
    invoice_trajet = read_text_file("data/expense_report/invoice_trajet.txt")
    expense_report_text = read_text_file("data/expense_report/expense_report.txt")

    # Create Stuff objects
    invoice_list_stuff = StuffFactory.make_stuff(
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
    expense_report_text_stuff = StuffFactory.make_stuff(
        concept_code="expense_report.ExpenseReportText",
        content=TextContent(text=expense_report_text),
        name="expense_report_text",
    )

    # Create Working Memory
    working_memory = WorkingMemoryFactory.make_from_multiple_stuffs([invoice_list_stuff, expense_report_text_stuff])

    # Run the pipe
    pipe_output = await run_pipe_code(
        pipe_code="process_expense_report",
        working_memory=working_memory,
    )

    # Log output and generate report
    pretty_print(pipe_output, title="Processing output for invoice")
    get_report_delegate().general_report()


Pipelex.make()
asyncio.run(process_expense_report())
