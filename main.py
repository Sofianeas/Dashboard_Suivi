from app.shell import AppConfig, WebApplication


config = AppConfig(
    title="IRIS Dashboard Help Desk",
    version="0.1.0",
)

app = WebApplication(config).create()
