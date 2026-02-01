import requests
import readchar
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.text import Text

# ================= CONFIG =================
API_URL = "https://samay.mygbu.in/api.php"
CONFIG_FILE = Path.home() / ".timetable_cli.json"
console = Console()

DAY_MAP = {
    1: "Monday", 2: "Tuesday", 3: "Wednesday",
    4: "Thursday", 5: "Friday", 6: "Saturday"
}

ASCII = """
██████╗ ██████╗ ██╗   ██╗
██╔════╝ ██╔══██╗██║   ██║
██║  ███╗██████╔╝██║   ██║
██║   ██║██╔══██╗██║   ██║
╚██████╔╝██████╔╝╚██████╔╝
 ╚═════╝ ╚═════╝  ╚═════╝
 TIMETABLE TERMINAL
"""

DATA = []  # loaded inside main()


# ================= NAV =================
class GoHome(Exception):
    pass


def read_nav_key():
    k = readchar.readkey()
    if k == "q":
        raise SystemExit
    if k == "m":
        raise GoHome()
    return k


# ================= CONFIG UTILS =================
def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(section_id, section_name):
    CONFIG_FILE.write_text(json.dumps({
        "section_id": str(section_id),
        "section_name": section_name
    }))


# ================= TIME UTILS =================
def generate_slots(start="08:30", duration=60, count=12):
    t = datetime.strptime(start, "%H:%M")
    slots = {}
    for i in range(1, count + 1):
        end = t + timedelta(minutes=duration)
        slots[i] = f"{t.strftime('%H:%M')}-{end.strftime('%H:%M')}"
        t = end
    return slots


def pretty(slot):
    s, e = slot.split("-")
    f = lambda x: datetime.strptime(x, "%H:%M").strftime("%I:%M %p")
    return f"{f(s)}-{f(e)}"


# ================= MENU =================
def key_menu(title, options):
    while True:
        console.clear()
        body = "\n".join(
            f"[cyan]{i+1}[/cyan] → {opt}"
            for i, opt in enumerate(options)
        )

        panel = Panel(
            Align.center(body),
            title=f"[bold]{title}",
            subtitle="number | b=back | m=menu | q=quit"
        )

        console.print(panel)
        try:
            k = read_nav_key()
        except SystemExit:
            raise

        if k == "b":
            return None
        if k.isdigit():
            idx = int(k) - 1
            if 0 <= idx < len(options):
                return options[idx]


# ================= TIMETABLE VIEW =================
def show_timetable(rows, title):
    table_map = defaultdict(lambda: defaultdict(list))
    periods = set()

    for x in rows:
        d = int(x["TT_Day"])
        p = int(x["TT_Period"])
        periods.add(p)

        subject = x.get("subject_name", "")
        sub_code = x.get("Subject_Code", "") or x.get("subject_code", "")
        teacher = x.get("TeacherName", "")
        room = x.get("RoomName", "")

        batch_raw = str(x.get("Batch_Id", "")).strip()
        batch = "G1" if batch_raw == "1" else "G2" if batch_raw == "2" else "CLASS"

        content = (
            f"[bold]{subject}[/bold]\n"
            f"[dim]{sub_code}[/dim]\n"
            f"[green]{teacher}[/green]\n"
            f"[white]{room}[/white]"
        )

        panel = Panel(
            content,
            title=batch,
            title_align="center",
            border_style="yellow" if batch == "G1" else "cyan" if batch == "G2" else "blue",
            padding=(0, 1),
        )

        table_map[d][p].append(panel)

    if not periods:
        console.print("[red]No timetable found[/red]")
        readchar.readkey()
        return

    maxp = max(periods)
    slots = generate_slots(count=maxp)

    table = Table(
        title=title,
        show_lines=True,
        border_style="bright_blue",
        caption="b=back | m=menu | q=quit"
    )

    table.add_column("Day", style="bold cyan", width=6)

    for p in range(1, maxp + 1):
        table.add_column(
            f"P{p}\n{pretty(slots[p])}",
            justify="center",
            width=14
        )

    for d in range(1, 7):
        row = [DAY_MAP[d][:3]]
        for p in range(1, maxp + 1):
            cell = table_map[d].get(p)
            if not cell:
                row.append("[dim]-[/dim]")
            elif len(cell) == 1:
                row.append(cell[0])
            else:
                row.append(Group(*cell))
        table.add_row(*row)

    console.clear()
    console.print(table)

    while True:
        try:
            k = read_nav_key()
            if k == "b":
                return
        except GoHome:
            return


# ================= HELPERS =================
def get_section_rows(section_id):
    return [x for x in DATA if str(x.get("Section_Id")) == str(section_id)]


def input_section_id():
    console.clear()
    console.print("[cyan]Enter Section ID:[/cyan] ", end="")
    return input().strip()


# ================= HOME =================
def home():
    cfg = load_config()
    console.clear()
    console.print(Align.center(Text(ASCII, style="bold cyan")))

    console.print(
        Align.center(
            "[1] View Saved Timetable → "
            + (f"[green]{cfg['section_name']}[/green]" if cfg else "[dim]Not set[/dim]")
        )
    )
    console.print(Align.center("[2] Browse & Select Section"))
    console.print(Align.center("[3] Enter Section ID (Direct)"))
    console.print(Align.center("[q] Quit"))

    return readchar.readkey()


# ================= MAIN ENTRY =================
def main():
    global DATA

    console.print("[cyan]Loading timetable data...[/cyan]")
    try:
        DATA = requests.get(API_URL, timeout=30).json()
    except Exception as e:
        console.print(f"[red]Failed to load data:[/red] {e}")
        return

    while True:
        try:
            key = home()

            if key == "1":
                cfg = load_config()
                if not cfg:
                    console.print("[red]No saved section yet[/red]")
                    readchar.readkey()
                    continue

                rows = get_section_rows(cfg["section_id"])
                show_timetable(rows, cfg["section_name"])

            elif key == "2":
                schools = sorted(set(x["school"] for x in DATA if x.get("school")))
                school = key_menu("Select School", schools)
                if not school:
                    continue

                d1 = [x for x in DATA if x["school"] == school]
                depts = sorted(set(x["StudentDepartment"] for x in d1))
                dept = key_menu("Select Department", depts)
                if not dept:
                    continue

                d2 = [x for x in d1 if x["StudentDepartment"] == dept]
                codes = sorted(set(x["Code"] for x in d2))
                code = key_menu("Select Code", codes)
                if not code:
                    continue

                d3 = [x for x in d2 if x["Code"] == code]
                sec_map = {
                    f"{x['SectionName']} ({x['Section_Id']})": x["Section_Id"]
                    for x in d3
                }

                sec_label = key_menu("Select Section", list(sec_map.keys()))
                if not sec_label:
                    continue

                sid = sec_map[sec_label]
                save_config(sid, sec_label)
                show_timetable(get_section_rows(sid), sec_label)

            elif key == "3":
                sid = input_section_id()
                rows = get_section_rows(sid)
                if not rows:
                    console.print("[red]Invalid Section ID[/red]")
                    readchar.readkey()
                    continue

                save_config(sid, f"Section {sid}")
                show_timetable(rows, f"Section {sid}")

        except GoHome:
            continue
        except SystemExit:
            break


# ================= SAFE ENTRY =================
if __name__ == "__main__":
    main()
