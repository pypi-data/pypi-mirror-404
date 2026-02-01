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
    http_url_to_repo: str
    default_branch: str | None
    empty_repo: bool


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
            "visibility": "public",
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
    def ensure_group_hierarchy(self, group_path: str) -> GroupInfo:
        """
        Ensure all groups in the path exist, creating them if needed.

        Parameters:
            group_path: Full group path (e.g., "docs" or "parent/docs")

        Returns:
            GroupInfo for the final group
        """
        parts = group_path.split("/")
        current_path = ""
        parent_id: int | None = None

        for part in parts:
            if current_path:
                current_path = f"{current_path}/{part}"
            else:
                current_path = part

            group = self.get_group(current_path)
            if group:
                parent_id = group.id
            else:
                logging.info(f"Creating group: {current_path}")
                group = self.create_group(name=part, path=part, parent_id=parent_id)
                parent_id = group.id

        # Return the final group (guaranteed to exist now)
        final_group = self.get_group(group_path)
        assert final_group is not None
        return final_group

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
                http_url_to_repo=item.get("http_url_to_repo", ""),
                default_branch=item.get("default_branch"),
                empty_repo=item.get("empty_repo", False),
            )
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    # ------------------------------------------------------------------------------------
    def create_project(self, name: str, namespace_id: int) -> ProjectInfo:
        """
        Create a new project configured for GitLab Pages.

        The project is created as private but with public Pages access,
        so documentation is publicly accessible while the source repo is not.

        Parameters:
            name: Project name
            namespace_id: Group/namespace ID to create project in

        Returns:
            Created ProjectInfo
        """
        data: dict[str, Any] = {
            "name": name,
            "namespace_id": namespace_id,
            "visibility": "private",
            "pages_access_level": "public",
            "initialize_with_readme": False,
        }

        item = self._request("POST", "/projects", data=data)
        return ProjectInfo(
            id=item["id"],
            name=item["name"],
            path=item["path"],
            path_with_namespace=item["path_with_namespace"],
            http_url_to_repo=item.get("http_url_to_repo", ""),
            default_branch=item.get("default_branch"),
            empty_repo=item.get("empty_repo", True),
        )

    # ------------------------------------------------------------------------------------
    def update_project_pages_access(self, project_id: int) -> None:
        """
        Update project to ensure Pages are publicly accessible.

        This is called after project creation to ensure the pages_access_level
        setting is applied correctly (it may not take effect during creation).

        Parameters:
            project_id: Project ID to update
        """
        data: dict[str, Any] = {
            "pages_access_level": "public",
        }
        self._request("PUT", f"/projects/{project_id}", data=data)
        logging.debug(f"Updated pages_access_level to public for project {project_id}")

    # ------------------------------------------------------------------------------------
    def ensure_project(self, group_path: str, project_name: str) -> ProjectInfo:
        """
        Ensure project exists, creating it if needed.

        Parameters:
            group_path: Group path where project should live
            project_name: Project name

        Returns:
            ProjectInfo for the project
        """
        project_path = f"{group_path}/{project_name}"
        project = self.get_project(project_path)

        if project:
            return project

        # Ensure group exists first
        group = self.ensure_group_hierarchy(group_path)

        # Create project
        logging.info(f"Creating project: {project_path}")
        project = self.create_project(name=project_name, namespace_id=group.id)

        # Explicitly set pages access to public (may not take effect during creation)
        self.update_project_pages_access(project.id)

        return project

    # ------------------------------------------------------------------------------------
    def get_pages_url(self, group_path: str, project_name: str) -> str:
        """
        Construct the GitLab Pages URL for a project.

        Parameters:
            group_path: Group path
            project_name: Project name

        Returns:
            Pages URL (e.g., https://group.gitlab.io/project/)
        """
        # Parse the base URL to extract the domain
        parsed = urllib.parse.urlparse(self.base_url)
        host = parsed.hostname or "gitlab.com"

        # GitLab Pages URL pattern:
        # https://<group>.<host>/<project>/
        # For nested groups: https://<root-group>.<host>/<subgroup>/<project>/

        # Split group path into root group and subgroups
        group_parts = group_path.split("/")
        root_group = group_parts[0]
        subgroups = "/".join(group_parts[1:]) if len(group_parts) > 1 else ""

        # Construct Pages domain
        if host == "gitlab.com":
            pages_domain = f"{root_group}.gitlab.io"
        else:
            # Self-hosted GitLab: typically <group>.pages.<domain>
            pages_domain = f"{root_group}.{host}"

        # Build the path
        if subgroups:
            path = f"/{subgroups}/{project_name}/"
        else:
            path = f"/{project_name}/"

        return f"https://{pages_domain}{path}"
