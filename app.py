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

DONATION_TYPES = [
    "Carbs",
    "Protein",
    "Vegetables",
    "Fruit"
]

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap"
        ),
        ui.tags.style("""
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
        """)
    ),
    
    ui.div(
        ui.tags.img(
            src="https://images.squarespace-cdn.com/content/v1/5622cd82e4b0501d40689558/cdab4aef-0027-40b7-9737-e2f893586a6a/Hopes_Corner_Logo_Green.png?format=750w",
            alt="Hope's Corner Logo",
            style="max-width: 300px; height: auto; display: block; margin: 0 auto;"
        ),
        ui.h3(
            "Donation Tracking System",
            class_="text-center mb-4",
            style="font-weight: 700; color: #2c5f2d; margin-top: 1rem;"
        ),
    ),
    
    ui.layout_columns(
        ui.card(
            ui.card_header(
                icon_svg("pen-to-square", height="1.2rem", width="1.2rem"),
                " Record New Donation"
            ),
            ui.input_text(
                "donor",
                "Donor Name",
                placeholder="Enter donor name"
            ),
            ui.input_text(
                "item_name",
                "Item Name",
                placeholder="Bread, Pastries, Apples"
            ),
            ui.row(
                ui.column(
                    6,
                    ui.input_select(
                        "donation_type",
                        "Category",
                        choices=DONATION_TYPES
                    )
                ),
                ui.column(
                    6,
                    ui.input_numeric(
                        "weight_lbs",
                        "Weight (lbs)",
                        value=0,
                        min=0,
                        step=0.01
                    )
                )
            ),
            ui.input_action_button(
                "submit",
                ui.span(
                    icon_svg("check", height="1rem", width="1rem"),
                    " Submit Donation"
                ),
                class_="btn-primary w-100 mt-3"
            ),
            ui.output_ui("submission_message")
        ),
        
        ui.card(
            ui.card_header(
                icon_svg("chart-line", height="1.2rem", width="1.2rem"),
                " Recent Donations"
            ),
            ui.output_ui("recent_donations")
        ),
        
        col_widths=[12, 12, 6, 6]
    ),
    theme=shinyswatch.theme.lux
)


def server(input, output, session):
    submission_status = reactive.Value("")
    refresh_trigger = reactive.Value(0)
    
    def get_supabase_client() -> Client:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    
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
            
            if input.weight_lbs() < 0:
                submission_status.set("error|Weight cannot be negative")
                return
            
            supabase = get_supabase_client()
            if not supabase:
                submission_status.set("error|Database connection not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env file")
                return
            
            donation_data = {
                "donor": input.donor().strip(),
                "item_name": input.item_name().strip(),
                "donation_type": input.donation_type(),
                "weight_lbs": float(input.weight_lbs()),
                "trays": 0.0
            }
            
            response = supabase.table("donations").insert(donation_data).execute()
            
            if response.data:
                submission_status.set("success|Donation recorded successfully!")
                ui.update_text("donor", value="")
                ui.update_text("item_name", value="")
                ui.update_numeric("weight_lbs", value=0)
                refresh_trigger.set(refresh_trigger.get() + 1)
            else:
                submission_status.set("error|Failed to record donation")
                
        except Exception as e:
            submission_status.set(f"error|Error: {str(e)}")
    
    @output
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
                    role="alert"
                ),
                class_="mt-4"
            )
        else:
            return ui.div(
                ui.tags.div(
                    icon_svg("circle-xmark", height="1.2rem", width="1.2rem"),
                    ui.tags.span(message, style="margin-left: 8px;"),
                    class_="alert alert-danger",
                    role="alert"
                ),
                class_="mt-4"
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
                    ui.p("Please configure SUPABASE_URL and SUPABASE_KEY", class_="text-muted"),
                    class_="text-center py-5"
                )
            
            response = supabase.table("donations").select("*").order(
                "donated_at", desc=True
            ).limit(10).execute()
            
            if not response.data:
                return ui.div(
                    icon_svg("box-open", height="3rem", width="3rem"),
                    ui.h5("No donations yet", class_="mt-3"),
                    ui.p("Submit your first donation to get started", class_="text-muted"),
                    class_="text-center py-5"
                )
            
            rows = []
            for donation in response.data:
                donated_at_utc = datetime.fromisoformat(
                    donation['donated_at'].replace('Z', '+00:00')
                )
                donated_at = donated_at_utc.astimezone(PACIFIC_TZ)
                formatted_date = donated_at.strftime("%m/%d/%y")
                formatted_time = donated_at.strftime("%I:%M %p")
                
                badge_colors = {
                    "Protein": "primary",
                    "Carbs": "warning",
                    "Vegetables": "success",
                    "Fruit": "danger"
                }
                badge_color = badge_colors.get(donation['donation_type'], "secondary")
                
                rows.append(
                    ui.tags.tr(
                        ui.tags.td(ui.tags.strong(donation['donor'])),
                        ui.tags.td(donation['item_name']),
                        ui.tags.td(
                            ui.tags.span(
                                donation['donation_type'],
                                class_=f"badge bg-{badge_color}"
                            )
                        ),
                        ui.tags.td(
                            ui.tags.strong(f"{donation['weight_lbs']:.1f}"),
                            " lbs"
                        ),
                        ui.tags.td(
                            ui.div(formatted_date),
                            ui.div(f"{formatted_time} PT", class_="text-muted small")
                        )
                    )
                )
            
            return ui.tags.table(
                ui.tags.thead(
                    ui.tags.tr(
                        ui.tags.th("Donor"),
                        ui.tags.th("Item"),
                        ui.tags.th("Category"),
                        ui.tags.th("Weight"),
                        ui.tags.th("Date")
                    )
                ),
                ui.tags.tbody(*rows),
                class_="table table-hover"
            )
            
        except Exception as e:
            return ui.div(
                icon_svg("triangle-exclamation", height="3rem", width="3rem"),
                ui.h5("Error Loading Data", class_="mt-3"),
                ui.p(str(e), class_="text-danger small"),
                class_="text-center py-5"
            )


app = App(app_ui, server)
