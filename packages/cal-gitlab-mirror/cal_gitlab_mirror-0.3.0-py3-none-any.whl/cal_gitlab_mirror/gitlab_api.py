# ----------------------------------------------------------------------------------------
#   gitlab_api
#   ----------
#
#   GitLab REST API client using urllib.request (stdlib only)
#
#   License
#   -------
#   MIT License - Copyright 2026 Cyber Assessment Labs
#
#   Authors
#   -------
#   bena (via claude)
#
#   Version History
#   ---------------
#   Jan 2026 - Created
# ----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------------------------

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

# ----------------------------------------------------------------------------------------
#   Types
# ----------------------------------------------------------------------------------------


@dataclass
class ProjectInfo:
    """Metadata about a GitLab project."""

    id: int
    name: str
    path: str
    path_with_namespace: str
    ssh_url_to_repo: str
    http_url_to_repo: str
    default_branch: str | None
    last_activity_at: str
    archived: bool
    empty_repo: bool
    marked_for_deletion: bool


@dataclass
class GroupInfo:
    """Metadata about a GitLab group."""

    id: int
    name: str
    path: str
    full_path: str
    parent_id: int | None


# ----------------------------------------------------------------------------------------
#   Classes
# ----------------------------------------------------------------------------------------


class GitLabClient:
    """
    GitLab API client using only stdlib (urllib.request).
    """

    # ------------------------------------------------------------------------------------
    def __init__(self, url: str, token: str):
        """
        Initialize GitLab connection.

        Parameters:
            url: GitLab instance URL (e.g., https://gitlab.com)
            token: Personal access token
        """
        self.base_url = url.rstrip("/")
        self.token = token
        self.api_url = f"{self.base_url}/api/v4"

    # ------------------------------------------------------------------------------------
    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make an API request.

        Parameters:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /projects)
            data: Request body data (for POST/PUT)
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        url = f"{self.api_url}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json",
        }

        body = json.dumps(data).encode() if data else None

        request = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request) as response:
                response_data = response.read().decode()
                return json.loads(response_data) if response_data else None
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else ""
            # 404 errors are expected when checking if resources exist
            if e.code == 404:
                logging.debug(f"GitLab API 404: {error_body}")
            else:
                logging.error(f"GitLab API error {e.code}: {error_body}")
            raise
        except urllib.error.URLError as e:
            logging.error(f"GitLab connection error: {e.reason}")
            raise

    # ------------------------------------------------------------------------------------
    def _paginate(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> list[Any]:
        """
        Fetch all pages of a paginated endpoint.

        Parameters:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Combined list of all items from all pages
        """
        if params is None:
            params = {}

        params["per_page"] = 100
        params["page"] = 1

        all_items: list[Any] = []

        while True:
            items = self._request("GET", endpoint, params=params)
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
            params["page"] += 1

        return all_items

    # ------------------------------------------------------------------------------------
    def list_group_projects(
        self, group_path: str, include_subgroups: bool = True
    ) -> list[ProjectInfo]:
        """
        List all projects in a group/namespace.

        Parameters:
            group_path: Group path (e.g., myorg/mygroup)
            include_subgroups: Whether to include projects from subgroups

        Returns:
            List of ProjectInfo objects
        """
        encoded_path = urllib.parse.quote(group_path, safe="")
        endpoint = f"/groups/{encoded_path}/projects"

        params: dict[str, Any] = {
            "include_subgroups": str(include_subgroups).lower(),
            "with_shared": "false",
        }

        items = self._paginate(endpoint, params)

        projects: list[ProjectInfo] = []
        for item in items:
            # Skip projects marked for deletion
            if item.get("marked_for_deletion_at") or item.get("marked_for_deletion_on"):
                continue
            projects.append(
                ProjectInfo(
                    id=item["id"],
                    name=item["name"],
                    path=item["path"],
                    path_with_namespace=item["path_with_namespace"],
                    ssh_url_to_repo=item.get("ssh_url_to_repo", ""),
                    http_url_to_repo=item.get("http_url_to_repo", ""),
                    default_branch=item.get("default_branch"),
                    last_activity_at=item.get("last_activity_at", ""),
                    archived=item.get("archived", False),
                    empty_repo=item.get("empty_repo", False),
                    marked_for_deletion=False,
                )
            )

        return projects

    # ------------------------------------------------------------------------------------
    def get_group(self, group_path: str) -> GroupInfo | None:
        """
        Get group information by path.

        Parameters:
            group_path: Full group path

        Returns:
            GroupInfo or None if not found
        """
        encoded_path = urllib.parse.quote(group_path, safe="")
        try:
            item = self._request("GET", f"/groups/{encoded_path}")
            return GroupInfo(
                id=item["id"],
                name=item["name"],
                path=item["path"],
                full_path=item["full_path"],
                parent_id=item.get("parent_id"),
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    # ------------------------------------------------------------------------------------
    def create_group(
        self, name: str, path: str, parent_id: int | None = None
    ) -> GroupInfo:
        """
        Create a new group.

        Parameters:
            name: Group name
            path: Group path (URL slug)
            parent_id: Parent group ID for subgroups

        Returns:
            Created GroupInfo
        """
        data: dict[str, Any] = {
            "name": name,
            "path": path,
            "visibility": "private",
        }
        if parent_id:
            data["parent_id"] = parent_id

        item = self._request("POST", "/groups", data=data)
        return GroupInfo(
            id=item["id"],
            name=item["name"],
            path=item["path"],
            full_path=item["full_path"],
            parent_id=item.get("parent_id"),
        )

    # ------------------------------------------------------------------------------------
    def get_project(self, project_path: str) -> ProjectInfo | None:
        """
        Get project by path.

        Parameters:
            project_path: Full project path (e.g., group/subgroup/project)

        Returns:
            ProjectInfo or None if not found
        """
        encoded_path = urllib.parse.quote(project_path, safe="")
        try:
            item = self._request("GET", f"/projects/{encoded_path}")
            return ProjectInfo(
                id=item["id"],
                name=item["name"],
                path=item["path"],
                path_with_namespace=item["path_with_namespace"],
                ssh_url_to_repo=item.get("ssh_url_to_repo", ""),
                http_url_to_repo=item.get("http_url_to_repo", ""),
                default_branch=item.get("default_branch"),
                last_activity_at=item.get("last_activity_at", ""),
                archived=item.get("archived", False),
                empty_repo=item.get("empty_repo", False),
                marked_for_deletion=bool(
                    item.get("marked_for_deletion_at")
                    or item.get("marked_for_deletion_on")
                ),
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    # ------------------------------------------------------------------------------------
    def create_project(self, name: str, namespace_id: int) -> ProjectInfo:
        """
        Create a new project.

        Parameters:
            name: Project name
            namespace_id: Group/namespace ID to create project in

        Returns:
            Created ProjectInfo
        """
        data = {
            "name": name,
            "namespace_id": namespace_id,
            "visibility": "private",
            "initialize_with_readme": False,
        }

        item = self._request("POST", "/projects", data=data)
        return ProjectInfo(
            id=item["id"],
            name=item["name"],
            path=item["path"],
            path_with_namespace=item["path_with_namespace"],
            ssh_url_to_repo=item.get("ssh_url_to_repo", ""),
            http_url_to_repo=item.get("http_url_to_repo", ""),
            default_branch=item.get("default_branch"),
            last_activity_at=item.get("last_activity_at", ""),
            archived=item.get("archived", False),
            empty_repo=item.get("empty_repo", True),
            marked_for_deletion=False,
        )

    # ------------------------------------------------------------------------------------
    def project_exists(self, project_path: str) -> bool:
        """Check if a project exists."""
        return self.get_project(project_path) is not None

    # ------------------------------------------------------------------------------------
    def list_protected_branches(self, project_id: int) -> list[str]:
        """
        List protected branch names for a project.

        Parameters:
            project_id: Project ID

        Returns:
            List of protected branch names
        """
        try:
            items = self._paginate(f"/projects/{project_id}/protected_branches")
            return [item["name"] for item in items]
        except urllib.error.HTTPError:
            return []

    # ------------------------------------------------------------------------------------
    def unprotect_branch(self, project_id: int, branch_name: str) -> bool:
        """
        Remove protection from a branch.

        Parameters:
            project_id: Project ID
            branch_name: Branch name to unprotect

        Returns:
            True on success, False on failure
        """
        encoded_branch = urllib.parse.quote(branch_name, safe="")
        try:
            self._request(
                "DELETE", f"/projects/{project_id}/protected_branches/{encoded_branch}"
            )
            return True
        except urllib.error.HTTPError:
            return False

    # ------------------------------------------------------------------------------------
    def protect_branch(
        self,
        project_id: int,
        branch_name: str,
        *,
        push_access_level: int = 40,
        merge_access_level: int = 40,
        allow_force_push: bool = False,
    ) -> bool:
        """
        Protect a branch.

        Parameters:
            project_id: Project ID
            branch_name: Branch name to protect
            push_access_level: Access level for push (40 = Maintainer)
            merge_access_level: Access level for merge (40 = Maintainer)
            allow_force_push: Whether to allow force push

        Returns:
            True on success, False on failure
        """
        data = {
            "name": branch_name,
            "push_access_level": push_access_level,
            "merge_access_level": merge_access_level,
            "allow_force_push": allow_force_push,
        }
        try:
            self._request(
                "POST", f"/projects/{project_id}/protected_branches", data=data
            )
            return True
        except urllib.error.HTTPError:
            return False
