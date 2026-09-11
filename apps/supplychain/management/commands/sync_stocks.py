from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from pytz import timezone as pytz_timezone
import os


class Command(BaseCommand):
    user_tz = pytz_timezone(getattr(settings, "DEFAULT_LOG_TIMEZONE", "Asia/Jakarta"))

    def log(self, message):
        timestamp = (
            timezone.now().astimezone(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
        )
        log_line = f"{timestamp}: {message}"
        print(log_line, flush=True)
        log_file = "/var/log/hiveforest/sync_stocks.log"
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

    def add_arguments(self, parser):
        parser.add_argument("--cby", type=int, required=False)  # 🔹 REQUIRED

    def handle(self, *args, **kwargs):
        help = "Sync OTS dan Daily Stock"
        cby_id = kwargs["cby"]
        self.log(f"🟢 Sync Started for user {cby_id}")
        try:
            call_command("load_stockdailymup", cby=cby_id)
            self.stdout.write(self.style.SUCCESS("Sync Daily Stock Complete"))
            self.log(f"Sync Daily Stock Complete")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Sync Daily Stock Failed: {e}"))
            self.log(f"Sync Daily Stock Failed: {e}")
            raise
