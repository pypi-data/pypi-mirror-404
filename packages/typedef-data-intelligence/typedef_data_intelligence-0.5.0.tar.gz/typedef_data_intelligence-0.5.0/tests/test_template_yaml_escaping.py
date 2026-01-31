"""Test YAML escaping in typedef config template."""
import yaml
from lineage.templates import render_typedef_config


def _base_kwargs(**overrides):
    """Return base kwargs for render_typedef_config with sensible defaults."""
    defaults = dict(
        project_name="test_project",
        dbt_path="/path/to/project",
        graph_db_path="/path/to/graph.db",
        typedef_home="/path/to/.typedef",
        profiles_dir="/path/to/profiles",
        snowflake_account="test",
        snowflake_user="test",
        snowflake_warehouse="test",
        snowflake_role="test",
        snowflake_database="test",
        snowflake_schema="PUBLIC",
        snowflake_private_key_path="/path/to/key",
        profile_name="dev",
    )
    defaults.update(overrides)
    return defaults


def test_template_handles_windows_paths():
    """Test that Windows paths with backslashes are properly escaped."""
    result = render_typedef_config(
        **_base_kwargs(
            dbt_path=r"C:\Users\test\project",
            graph_db_path=r"C:\Users\test\.typedef\graph.db",
            typedef_home=r"C:\Users\test\.typedef",
            snowflake_private_key_path=r"C:\Users\test\keys\rsa_key.p8",
        )
    )

    # Should be valid YAML
    config = yaml.safe_load(result)
    assert config["projects"]["test_project"]["dbt_path"] == r"C:\Users\test\project"


def test_template_handles_quotes_in_values():
    """Test that values with double quotes are properly escaped."""
    result = render_typedef_config(
        **_base_kwargs(snowflake_account='test"account')
    )

    # Should be valid YAML
    config = yaml.safe_load(result)
    assert config["data"]["account"] == 'test"account'


def test_template_handles_colons_in_project_name():
    """Test that project names with colons are properly quoted as YAML keys."""
    result = render_typedef_config(
        **_base_kwargs(project_name="project:with:colons")
    )

    # Should be valid YAML
    config = yaml.safe_load(result)
    assert "project:with:colons" in config["projects"]


def test_template_handles_project_env_vars_with_special_chars():
    """Test that project_env_vars with special characters are properly escaped."""
    result = render_typedef_config(
        **_base_kwargs(
            project_env_vars={
                "PATH": r"C:\Users\test\bin;C:\Program Files\app",
                "QUOTED": 'value with "quotes"',
                "NEWLINE": "line1\nline2",
                "COLON:KEY": "value:with:colons",
            },
        )
    )

    # Should be valid YAML
    config = yaml.safe_load(result)
    env_vars = config["projects"]["test_project"]["env"]
    assert env_vars["PATH"] == r"C:\Users\test\bin;C:\Program Files\app"
    assert env_vars["QUOTED"] == 'value with "quotes"'
    assert env_vars["NEWLINE"] == "line1\nline2"
    assert "COLON:KEY" in env_vars


def test_template_handles_newlines_in_values():
    """Test that values with newlines are properly escaped."""
    result = render_typedef_config(
        **_base_kwargs(default_database="db\nwith\nnewlines")
    )

    # Should be valid YAML
    config = yaml.safe_load(result)
    assert config["projects"]["test_project"]["default_database"] == "db\nwith\nnewlines"


def test_template_renders_git_config_when_enabled():
    """Test that git config block is rendered when git_enabled=True."""
    result = render_typedef_config(
        **_base_kwargs(
            git_enabled=True,
            git_working_directory="/path/to/git/repo",
        )
    )

    config = yaml.safe_load(result)
    project = config["projects"]["test_project"]
    assert "git" in project
    assert project["git"]["enabled"] is True
    assert project["git"]["working_directory"] == "/path/to/git/repo"


def test_template_omits_git_config_when_disabled():
    """Test that git config block is omitted when git_enabled=False."""
    result = render_typedef_config(
        **_base_kwargs(git_enabled=False)
    )

    config = yaml.safe_load(result)
    project = config["projects"]["test_project"]
    assert "git" not in project
