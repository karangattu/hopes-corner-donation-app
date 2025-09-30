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
            href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
        ),
        ui.tags.style("""
            :root {
                --primary-color: #2563eb;
                --primary-dark: #1e40af;
                --success-color: #10b981;
                --success-dark: #059669;
                --danger-color: #ef4444;
                --warning-color: #f59e0b;
                --background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --card-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                --card-hover-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
            }
            
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            body {
                background: var(--background);
                min-height: 100vh;
                padding: 20px 0;
            }
            
            .app-header {
                text-align: center;
                padding: 40px 20px;
                margin-bottom: 30px;
            }
            
            .app-title {
                color: white;
                font-size: 3rem;
                font-weight: 700;
                margin: 0 0 10px 0;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
                letter-spacing: -1px;
            }
            
            .app-subtitle {
                color: rgba(255, 255, 255, 0.95);
                font-size: 1.25rem;
                font-weight: 400;
                margin: 0;
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .main-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
            }
            
            .card {
                background: white;
                border-radius: 20px;
                box-shadow: var(--card-shadow);
                border: none;
                transition: all 0.3s ease;
                height: 100%;
                overflow: hidden;
            }
            
            .card:hover {
                box-shadow: var(--card-hover-shadow);
                transform: translateY(-2px);
            }
            
            .card-header {
                background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                color: white;
                padding: 25px 30px;
                border: none;
                border-radius: 20px 20px 0 0 !important;
            }
            
            .card-header.success-header {
                background: linear-gradient(135deg, var(--success-color), var(--success-dark));
            }
            
            .card-header h3 {
                margin: 0;
                font-size: 1.5rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .card-icon {
                font-size: 1.5rem;
                opacity: 0.95;
            }
            
            .card-body {
                padding: 35px 30px;
            }
            
            .form-label {
                font-weight: 600;
                color: #374151;
                margin-bottom: 8px;
                font-size: 0.95rem;
                letter-spacing: 0.3px;
            }
            
            .form-control, .form-select {
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 1rem;
                transition: all 0.2s ease;
                background: #f9fafb;
            }
            
            .form-control:focus, .form-select:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
                background: white;
                outline: none;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                border: none;
                border-radius: 12px;
                padding: 16px 32px;
                font-size: 1.1rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
                letter-spacing: 0.5px;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
            }
            
            .btn-primary:active {
                transform: translateY(0);
            }
            
            .alert {
                border-radius: 12px;
                border: none;
                padding: 16px 20px;
                font-weight: 500;
                animation: slideIn 0.3s ease;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .alert-success {
                background: #d1fae5;
                color: #065f46;
                border-left: 4px solid var(--success-color);
            }
            
            .alert-danger {
                background: #fee2e2;
                color: #991b1b;
                border-left: 4px solid var(--danger-color);
            }
            
            .table-container {
                max-height: 600px;
                overflow-y: auto;
                border-radius: 12px;
            }
            
            .table {
                margin: 0;
                font-size: 0.95rem;
            }
            
            .table thead {
                position: sticky;
                top: 0;
                z-index: 10;
            }
            
            .table thead th {
                background: linear-gradient(135deg, #f8fafc, #f1f5f9);
                color: #1e293b;
                font-weight: 600;
                padding: 16px 20px;
                border: none;
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 0.5px;
            }
            
            .table tbody tr {
                transition: all 0.2s ease;
                border-bottom: 1px solid #f1f5f9;
            }
            
            .table tbody tr:hover {
                background: #f8fafc;
                transform: scale(1.01);
            }
            
            .table tbody td {
                padding: 18px 20px;
                color: #475569;
                vertical-align: middle;
            }
            
            .donation-type-badge {
                display: inline-block;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .badge-protein { background: #dbeafe; color: #1e40af; }
            .badge-carbs { background: #fef3c7; color: #92400e; }
            .badge-vegetables { background: #d1fae5; color: #065f46; }
            .badge-fruit { background: #fce7f3; color: #9f1239; }
            
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #94a3b8;
            }
            
            .empty-state-icon {
                margin-bottom: 20px;
                opacity: 0.4;
                color: #94a3b8;
            }
            
            .empty-state-icon svg {
                vertical-align: middle;
            }
            
            .empty-state-text {
                font-size: 1.1rem;
                font-weight: 500;
            }
            
            /* Mobile responsive */
            @media (max-width: 768px) {
                .app-title {
                    font-size: 2rem;
                }
                
                .app-subtitle {
                    font-size: 1rem;
                }
                
                .card-body {
                    padding: 25px 20px;
                }
                
                .table {
                    font-size: 0.85rem;
                }
                
                .table thead th,
                .table tbody td {
                    padding: 12px 10px;
                }
            }
            
            /* Scrollbar styling */
            .table-container::-webkit-scrollbar {
                width: 8px;
            }
            
            .table-container::-webkit-scrollbar-track {
                background: #f1f5f9;
                border-radius: 10px;
            }
            
            .table-container::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 10px;
            }
            
            .table-container::-webkit-scrollbar-thumb:hover {
                background: #94a3b8;
            }
        """)
    ),
    
    ui.div(
        ui.h1("Hope's Corner", class_="app-title"),
        ui.p("Donation Tracking System", class_="app-subtitle"),
        class_="app-header"
    ),
    
    ui.div(
        ui.layout_columns(
            ui.card(
                ui.div(
                    ui.h3(
                        icon_svg("pen-to-square", height="1.5rem", width="1.5rem"),
                        "Record New Donation",
                        class_="mb-0"
                    ),
                    class_="card-header"
                ),
                ui.div(
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
                            icon_svg("check", height="1.1rem", width="1.1rem"),
                            " Submit Donation"
                        ),
                        class_="btn-primary w-100 mt-4"
                    ),
                    ui.output_ui("submission_message"),
                    class_="card-body"
                )
            ),
            
            ui.card(
                ui.div(
                    ui.h3(
                        icon_svg("chart-line", height="1.5rem", width="1.5rem"),
                        "Recent Donations",
                        class_="mb-0"
                    ),
                    class_="card-header success-header"
                ),
                ui.div(
                    ui.output_ui("recent_donations"),
                    class_="card-body",
                    style="padding: 0;"
                )
            ),
            
            col_widths=[12, 12, 6, 6]
        ),
        class_="main-container"
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
                    ui.div(
                        ui.div(
                            icon_svg("plug", height="4rem", width="4rem"),
                            class_="empty-state-icon"
                        ),
                        ui.div("Database Not Connected", class_="empty-state-text"),
                        ui.div(
                            "Please configure SUPABASE_URL and SUPABASE_KEY",
                            style="font-size: 0.9rem; margin-top: 10px;"
                        ),
                        class_="empty-state"
                    )
                )
            
            response = supabase.table("donations").select("*").order(
                "donated_at", desc=True
            ).limit(10).execute()
            
            if not response.data:
                return ui.div(
                    ui.div(
                        ui.div(
                            icon_svg("box-open", height="4rem", width="4rem"),
                            class_="empty-state-icon"
                        ),
                        ui.div("No donations yet", class_="empty-state-text"),
                        ui.div(
                            "Submit your first donation to get started",
                            style="font-size: 0.9rem; margin-top: 10px;"
                        ),
                        class_="empty-state"
                    )
                )
            
            rows = []
            for donation in response.data:
                donated_at_utc = datetime.fromisoformat(
                    donation['donated_at'].replace('Z', '+00:00')
                )
                donated_at = donated_at_utc.astimezone(PACIFIC_TZ)
                formatted_date = donated_at.strftime("%m/%d/%y")
                formatted_time = donated_at.strftime("%I:%M %p")
                
                badge_map = {
                    "Protein": "badge-protein",
                    "Carbs": "badge-carbs",
                    "Vegetables": "badge-vegetables",
                    "Fruit": "badge-fruit"
                }
                badge_class = badge_map.get(
                    donation['donation_type'],
                    "badge-protein"
                )
                
                rows.append(
                    ui.tags.tr(
                        ui.tags.td(
                            ui.tags.strong(donation['donor']),
                            style="color: #1e293b;"
                        ),
                        ui.tags.td(donation['item_name']),
                        ui.tags.td(
                            ui.tags.span(
                                donation['donation_type'],
                                class_=f"donation-type-badge {badge_class}"
                            )
                        ),
                        ui.tags.td(
                            ui.tags.strong(f"{donation['weight_lbs']:.1f}"),
                            " lbs"
                        ),
                        ui.tags.td(
                            ui.div(formatted_date, style="font-weight: 500;"),
                            ui.div(
                                f"{formatted_time} PT",
                                style="font-size: 0.85rem; color: #94a3b8;"
                            )
                        )
                    )
                )
            
            return ui.div(
                ui.tags.table(
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
                    class_="table"
                ),
                class_="table-container"
            )
            
        except Exception as e:
            return ui.div(
                ui.div(
                    ui.div(
                        icon_svg(
                            "triangle-exclamation",
                            height="4rem",
                            width="4rem"
                        ),
                        class_="empty-state-icon"
                    ),
                    ui.div("Error Loading Data", class_="empty-state-text"),
                    ui.div(
                        str(e),
                        style="font-size: 0.85rem; margin-top: 10px; color: #ef4444;"
                    ),
                    class_="empty-state"
                )
            )


app = App(app_ui, server)
