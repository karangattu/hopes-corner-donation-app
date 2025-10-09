import os
from datetime import datetime
from zoneinfo import ZoneInfo

import shinyswatch
from dotenv import load_dotenv
from faicons import icon_svg
from shiny import App, reactive, render, ui
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")

DONATION_TYPES = ["Carbs", "Protein", "Vegetables", "Fruit"]

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap",
        ),
        ui.tags.style(
            """
            * {
                font-family: 'Lato', sans-serif;
            }
            label {
                font-weight: 700;
            }
            .card-header {
                font-size: 1.5rem;
                font-weight: 700;
            }
        """
        ),
    ),
    ui.div(
        ui.tags.img(
            src="https://images.squarespace-cdn.com/content/v1/5622cd82e4b0501d40689558/cdab4aef-0027-40b7-9737-e2f893586a6a/Hopes_Corner_Logo_Green.png?format=750w",
            alt="Hope's Corner Logo",
            style="max-width: 300px; height: auto; display: block; margin: 0 auto;",
        ),
        ui.h3(
            "Donation Tracking System",
            class_="text-center mb-4",
            style="font-weight: 700; color: #2c5f2d; margin-top: 1rem;",
        ),
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header(
                icon_svg("pen-to-square", height="1.2rem", width="1.2rem"),
                " Record New Donation",
            ),
            ui.output_ui("quick_add_buttons"),
            ui.input_text("donor", "Donor Name", placeholder="Enter donor name"),
            ui.input_text(
                "item_name", "Item Name", placeholder="Bread, Pastries, Apples"
            ),
            ui.input_select("donation_type", "Category", choices=DONATION_TYPES),
            ui.input_radio_buttons(
                "quantity_type",
                "Measurement Type",
                choices=["Weight", "Trays"],
                selected="Weight",
                inline=True,
            ),
            ui.output_ui("quantity_input"),
            ui.input_action_button(
                "submit",
                ui.span(
                    icon_svg("check", height="1rem", width="1rem"), " Submit Donation"
                ),
                class_="btn-primary w-100 mt-3",
            ),
            ui.output_ui("submission_message"),
        ),
        ui.card(
            ui.card_header(
                icon_svg("chart-line", height="1.2rem", width="1.2rem"),
                " Recent Donations",
            ),
            ui.div(
                ui.input_action_button(
                    "undo",
                    ui.span(
                        icon_svg("rotate-left", height="1rem", width="1rem"),
                        " Undo Last Entry",
                    ),
                    class_="btn-warning btn-sm mb-3",
                ),
                class_="d-flex justify-content-end",
            ),
            ui.output_ui("recent_donations"),
            ui.output_ui("undo_message"),
        ),
        col_widths=[12, 12, 6, 6],
    ),
    theme=shinyswatch.theme.lux,
)


def server(input, output, session):
    submission_status = reactive.Value("")
    undo_status = reactive.Value("")
    refresh_trigger = reactive.Value(0)
    quantity_value = reactive.Value(None)
    quick_add_state = reactive.Value([])
    quick_add_last_counts = reactive.Value({})

    def get_supabase_client() -> Client:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        return create_client(SUPABASE_URL, SUPABASE_KEY)

    @output
    @render.ui
    def quantity_input():
        if input.quantity_type() == "Weight":
            return ui.input_numeric(
                "quantity_value",
                "Weight (lbs)",
                value=quantity_value.get(),
                min=0,
                step=0.01,
            )
        else:
            return ui.input_numeric(
                "quantity_value",
                "Number of Trays",
                value=quantity_value.get(),
                min=0,
                step=1,
            )

    @render.ui
    def quick_add_buttons():
        combos = quick_add_state.get()

        if not combos:
            return ui.div(
                ui.tags.small(
                    "Quick add suggestions appear after you log donations.",
                    class_="text-muted",
                ),
                class_="mt-3",
            )

        buttons = []
        for idx, combo in enumerate(combos):
            label = (
                f"{combo['donor']} · {combo['item_name']} "
                f"({combo['donation_type']})"
            )
            buttons.append(
                ui.input_action_button(
                    f"quick_add_{idx}",
                    label,
                    class_="btn-outline-secondary btn-sm me-2 mb-2",
                )
            )

        return ui.div(
            ui.tags.small("Quick add recent items:", class_="text-muted d-block mb-2"),
            ui.div(*buttons, class_="d-flex flex-wrap"),
            class_="mt-3",
        )

    @reactive.Effect
    def load_quick_add_options():
        _ = refresh_trigger.get()

        supabase = get_supabase_client()
        if not supabase:
            quick_add_state.set([])
            quick_add_last_counts.set({})
            return

        try:
            response = (
                supabase.table("donations")
                .select("donor,item_name,donation_type")
                .order("donated_at", desc=True)
                .limit(25)
                .execute()
            )
            combos = []
            seen = set()
            for record in response.data or []:
                donor = record.get("donor")
                item_name = record.get("item_name")
                donation_type = record.get("donation_type")
                signature = (donor, item_name, donation_type)
                if None in signature:
                    continue
                if signature in seen:
                    continue
                seen.add(signature)
                combos.append(
                    {
                        "donor": donor,
                        "item_name": item_name,
                        "donation_type": donation_type,
                    }
                )
                if len(combos) == 3:
                    break
            quick_add_state.set(combos)
            quick_add_last_counts.set({})
        except Exception:
            quick_add_state.set([])
            quick_add_last_counts.set({})

    @reactive.Effect
    def handle_quick_add_clicks():
        combos = quick_add_state.get()
        last_counts = quick_add_last_counts.get()
        updated_counts = dict(last_counts)

        for idx, combo in enumerate(combos):
            btn_id = f"quick_add_{idx}"
            btn = getattr(input, btn_id, None)
            if btn is None:
                updated_counts.pop(btn_id, None)
                continue
            count = btn() or 0
            previous = last_counts.get(btn_id, 0)
            if count > previous:
                ui.update_text("donor", value=combo["donor"])
                ui.update_text("item_name", value=combo["item_name"])
                ui.update_select("donation_type", selected=combo["donation_type"])
                quantity_value.set(None)
            updated_counts[btn_id] = count

        if updated_counts != last_counts:
            quick_add_last_counts.set(updated_counts)

    @reactive.Effect
    @reactive.event(input.submit)
    def submit_donation():
        try:
            if not input.donor().strip():
                submission_status.set("error|Please enter a donor name")
                return

            if not input.item_name().strip():
                submission_status.set("error|Please enter an item name")
                return

            value = input.quantity_value()

            if value is None or value <= 0:
                if input.quantity_type() == "Weight":
                    measurement = "weight"
                else:
                    measurement = "number of trays"
                submission_status.set(f"error|Please enter a valid {measurement}")
                return

            if value < 0:
                submission_status.set("error|Value cannot be negative")
                return

            supabase = get_supabase_client()
            if not supabase:
                submission_status.set(
                    "error|Database connection not configured. "
                    "Please set SUPABASE_URL and SUPABASE_KEY in .env file"
                )
                return

            is_weight = input.quantity_type() == "Weight"
            donation_data = {
                "donor": input.donor().strip(),
                "item_name": input.item_name().strip(),
                "donation_type": input.donation_type(),
                "weight_lbs": float(value) if is_weight else 0.0,
                "trays": float(value) if not is_weight else 0.0,
            }

            response = supabase.table("donations").insert(donation_data).execute()

            if response.data:
                submission_status.set("success|Donation recorded successfully!")
                ui.update_text("donor", value="")
                ui.update_text("item_name", value="")
                quantity_value.set(None)
                refresh_trigger.set(refresh_trigger.get() + 1)
            else:
                submission_status.set("error|Failed to record donation")

        except Exception as e:
            submission_status.set(f"error|Error: {str(e)}")

    @reactive.Effect
    @reactive.event(input.undo)
    def undo_last_donation():
        try:
            supabase = get_supabase_client()
            if not supabase:
                undo_status.set("error|Database connection not configured")
                return

            response = (
                supabase.table("donations")
                .select("*")
                .order("donated_at", desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                undo_status.set("error|No donations to undo")
                return

            last_donation = response.data[0]
            delete_response = (
                supabase.table("donations")
                .delete()
                .eq("id", last_donation["id"])
                .execute()
            )

            if delete_response:
                donor_name = last_donation["donor"]
                item_name = last_donation["item_name"]
                undo_status.set(f"success|Undone: {donor_name} - {item_name}")
                refresh_trigger.set(refresh_trigger.get() + 1)
            else:
                undo_status.set("error|Failed to undo donation")

        except Exception as e:
            undo_status.set(f"error|Error: {str(e)}")

    @render.ui
    def submission_message():
        status = submission_status.get()

        if not status:
            return ui.div()

        status_type, message = status.split("|", 1)

        if status_type == "success":
            return ui.div(
                ui.tags.div(
                    icon_svg("circle-check", height="1.2rem", width="1.2rem"),
                    ui.tags.span(message, style="margin-left: 8px;"),
                    class_="alert alert-success",
                    role="alert",
                ),
                class_="mt-4",
            )
        else:
            return ui.div(
                ui.tags.div(
                    icon_svg("circle-xmark", height="1.2rem", width="1.2rem"),
                    ui.tags.span(message, style="margin-left: 8px;"),
                    class_="alert alert-danger",
                    role="alert",
                ),
                class_="mt-4",
            )

    @render.ui
    def undo_message():
        status = undo_status.get()

        if not status:
            return ui.div()

        status_type, message = status.split("|", 1)

        if status_type == "success":
            return ui.div(
                ui.tags.div(
                    icon_svg("circle-check", height="1rem", width="1rem"),
                    ui.tags.span(message, style="margin-left: 8px;"),
                    class_="alert alert-success alert-dismissible fade show",
                    role="alert",
                ),
                class_="mt-3",
            )
        else:
            return ui.div(
                ui.tags.div(
                    icon_svg("circle-xmark", height="1rem", width="1rem"),
                    ui.tags.span(message, style="margin-left: 8px;"),
                    class_="alert alert-warning alert-dismissible fade show",
                    role="alert",
                ),
                class_="mt-3",
            )

    @output
    @render.ui
    def recent_donations():
        _ = refresh_trigger.get()

        try:
            supabase = get_supabase_client()
            if not supabase:
                return ui.div(
                    icon_svg("plug", height="3rem", width="3rem"),
                    ui.h5("Database Not Connected", class_="mt-3"),
                    ui.p(
                        "Please configure SUPABASE_URL and SUPABASE_KEY",
                        class_="text-muted",
                    ),
                    class_="text-center py-5",
                )

            response = (
                supabase.table("donations")
                .select("*")
                .order("donated_at", desc=True)
                .limit(10)
                .execute()
            )

            if not response.data:
                return ui.div(
                    icon_svg("box-open", height="3rem", width="3rem"),
                    ui.h5("No donations yet", class_="mt-3"),
                    ui.p(
                        "Submit your first donation to get started", class_="text-muted"
                    ),
                    class_="text-center py-5",
                )

            rows = []
            for donation in response.data:
                donated_at_utc = datetime.fromisoformat(
                    donation["donated_at"].replace("Z", "+00:00")
                )
                donated_at = donated_at_utc.astimezone(PACIFIC_TZ)
                formatted_date = donated_at.strftime("%m/%d/%y")
                formatted_time = donated_at.strftime("%I:%M %p")

                badge_colors = {
                    "Protein": "primary",
                    "Carbs": "warning",
                    "Vegetables": "success",
                    "Fruit": "danger",
                }
                badge_color = badge_colors.get(donation["donation_type"], "secondary")

                weight_lbs = donation.get("weight_lbs", 0) or 0
                trays = donation.get("trays", 0) or 0

                if weight_lbs > 0:
                    quantity_display = ui.tags.td(
                        ui.tags.strong(f"{weight_lbs:.1f}"), " lbs"
                    )
                elif trays > 0:
                    quantity_display = ui.tags.td(
                        ui.tags.strong(f"{int(trays)}"), " trays"
                    )
                else:
                    quantity_display = ui.tags.td(
                        ui.tags.span("N/A", class_="text-muted")
                    )

                rows.append(
                    ui.tags.tr(
                        ui.tags.td(ui.tags.strong(donation["donor"])),
                        ui.tags.td(donation["item_name"]),
                        ui.tags.td(
                            ui.tags.span(
                                donation["donation_type"],
                                class_=f"badge bg-{badge_color}",
                            )
                        ),
                        quantity_display,
                        ui.tags.td(
                            ui.div(formatted_date),
                            ui.div(f"{formatted_time} PT", class_="text-muted small"),
                        ),
                    )
                )

            return ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("Donor"),
                        ui.tags.th("Item"),
                        ui.tags.th("Category"),
                        ui.tags.th("Quantity"),
                        ui.tags.th("Date"),
                    )
                ),
                ui.tags.tbody(*rows),
                class_="table table-hover",
            )

        except Exception as e:
            return ui.div(
                icon_svg("triangle-exclamation", height="3rem", width="3rem"),
                ui.h5("Error Loading Data", class_="mt-3"),
                ui.p(str(e), class_="text-danger small"),
                class_="text-center py-5",
            )


app = App(app_ui, server)
