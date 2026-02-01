"""Jobs resource for the Armor SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from anomalyarmor.client import Client


class JobsResource:
    """Resource for job status operations."""

    def __init__(self, client: Client) -> None:
        """Initialize the jobs resource.

        Args:
            client: The parent client instance
        """
        self._client = client

    def status(self, job_id: str) -> dict[str, Any]:
        """Get the status of a job.

        Args:
            job_id: Job UUID

        Returns:
            Job status information including:
                - job_id: Job UUID
                - status: pending, running, completed, or failed
                - workflow_name: Name of the workflow
                - asset_id: Associated asset UUID
                - progress: Progress percentage (0-100)
                - error: Error message if failed
                - created_at: Job creation timestamp
                - completed_at: Job completion timestamp

        Example:
            >>> status = client.jobs.status("b74fc72f-0332-427e-b508-e718f7b71a5d")
            >>> print(status["status"])
            "completed"
        """
        response = self._client._request("GET", f"/sdk/jobs/{job_id}")
        data: dict[str, Any] = response.get("data", {})
        return data
