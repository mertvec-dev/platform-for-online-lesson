"""Pre-startup hook: прогон тестов перед запуском приложения."""

import subprocess

from backend.api.core.config import settings


def run_tests() -> None:
    """Запускает pytest. При падении — выбрасывает RuntimeError."""
    if settings.ENVIRONMENT == "development":
        return  # в dev не блокируем запуск

    result = subprocess.run(
        ["python", "-m", "pytest", "backend/tests/", "-q", "--tb=short"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Pre-startup тесты провалены:\n{result.stdout}\n{result.stderr}"
        )
