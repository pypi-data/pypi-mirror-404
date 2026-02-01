"""
Tests for app deployment CLI commands
"""

import pytest
from click.testing import CliRunner
from varitykit.commands.app_deploy import app


class TestAppDeployCommand:
    """Test suite for app deploy command"""

    def test_app_group_help(self):
        """Test that app group shows help"""
        runner = CliRunner()
        result = runner.invoke(app, ['--help'])

        assert result.exit_code == 0
        assert 'Deploy and manage applications' in result.output
        assert 'deploy' in result.output
        assert 'list' in result.output
        assert 'info' in result.output

    def test_deploy_help(self):
        """Test that deploy command shows help"""
        runner = CliRunner()
        result = runner.invoke(app, ['deploy', '--help'])

        assert result.exit_code == 0
        assert 'Deploy application to decentralized infrastructure' in result.output
        assert '--network' in result.output
        assert '--submit-to-store' in result.output
        assert '--path' in result.output

    def test_deploy_default_options(self, tmp_path, mocker):
        """Test deploy command with default options"""
        runner = CliRunner()

        # Create a simple test directory
        test_dir = tmp_path / "test-app"
        test_dir.mkdir()
        (test_dir / "package.json").write_text('{"name": "test-app"}')

        # Mock the DeploymentOrchestrator
        mock_orchestrator = mocker.patch('varitykit.commands.app_deploy.DeploymentOrchestrator')
        mock_result = mocker.Mock()
        mock_result.frontend_url = "https://ipfs.io/ipfs/QmTest123"
        mock_result.thirdweb_url = "https://gateway.thirdweb.com/ipfs/QmTest123"
        mock_result.cid = "QmTest123"
        mock_result.deployment_id = "deploy-1737492000"
        mock_result.app_store_url = None
        mock_orchestrator.return_value.deploy.return_value = mock_result

        result = runner.invoke(app, ['deploy', '--path', str(test_dir)], obj={'logger': mocker.Mock()})

        # Command should succeed
        assert result.exit_code == 0
        assert 'Varity App Deployment' in result.output

    def test_deploy_with_network_option(self, tmp_path):
        """Test deploy command with network option"""
        runner = CliRunner()

        test_dir = tmp_path / "test-app"
        test_dir.mkdir()

        result = runner.invoke(app, ['deploy', '--network', 'varity', '--path', str(test_dir)])

        assert 'Network:' in result.output
        assert 'varity' in result.output.lower()

    def test_deploy_with_submit_to_store(self, tmp_path):
        """Test deploy command with submit-to-store flag"""
        runner = CliRunner()

        test_dir = tmp_path / "test-app"
        test_dir.mkdir()

        result = runner.invoke(app, [
            'deploy',
            '--submit-to-store',
            '--path', str(test_dir)
        ])

        assert 'Phase 2 feature' in result.output

    def test_deploy_nonexistent_path(self):
        """Test deploy command with non-existent path"""
        runner = CliRunner()

        result = runner.invoke(app, ['deploy', '--path', '/nonexistent/path'])

        # Should fail because path doesn't exist
        assert result.exit_code != 0

    def test_list_command(self):
        """Test list command"""
        runner = CliRunner()
        result = runner.invoke(app, ['list'])

        assert result.exit_code == 0
        assert 'Recent Deployments' in result.output
        assert 'Phase 2' in result.output

    def test_info_command(self):
        """Test info command"""
        runner = CliRunner()
        result = runner.invoke(app, ['info', 'deploy-1737492000'])

        assert result.exit_code == 0
        assert 'Deployment:' in result.output
        assert 'deploy-1737492000' in result.output

    def test_status_command(self):
        """Test status command"""
        runner = CliRunner()
        result = runner.invoke(app, ['status'])

        assert result.exit_code == 0
        assert 'Deployment Status' in result.output

    def test_status_with_network_filter(self):
        """Test status command with network filter"""
        runner = CliRunner()
        result = runner.invoke(app, ['status', '--network', 'varity'])

        assert result.exit_code == 0
        assert 'varity' in result.output.lower()

    def test_rollback_command(self):
        """Test rollback command"""
        runner = CliRunner()
        result = runner.invoke(app, ['rollback', 'deploy-1737492000'])

        assert result.exit_code == 0
        assert 'Rollback' in result.output


class TestAppDeployIntegration:
    """Integration tests for app deploy command"""

    @pytest.mark.integration
    def test_deploy_sample_nextjs_app(self, tmp_path):
        """Test deploying a sample Next.js app"""
        runner = CliRunner()

        # Create a mock Next.js app structure
        app_dir = tmp_path / "nextjs-app"
        app_dir.mkdir()

        (app_dir / "package.json").write_text('''{
            "name": "nextjs-app",
            "dependencies": {
                "next": "14.0.0",
                "react": "18.0.0"
            },
            "scripts": {
                "build": "next build"
            }
        }''')

        (app_dir / "next.config.js").write_text('''
module.exports = {
  output: 'export'
}
        ''')

        result = runner.invoke(app, ['deploy', '--path', str(app_dir)])

        # Should detect as Next.js project
        assert 'Project:' in result.output

    @pytest.mark.integration
    def test_deploy_sample_react_app(self, tmp_path):
        """Test deploying a sample React app"""
        runner = CliRunner()

        # Create a mock React app structure
        app_dir = tmp_path / "react-app"
        app_dir.mkdir()

        (app_dir / "package.json").write_text('''{
            "name": "react-app",
            "dependencies": {
                "react": "18.0.0",
                "react-scripts": "5.0.0"
            },
            "scripts": {
                "build": "react-scripts build"
            }
        }''')

        result = runner.invoke(app, ['deploy', '--path', str(app_dir)])

        assert 'Project:' in result.output


# Fixtures
@pytest.fixture
def mock_deployment_orchestrator(mocker):
    """Mock the DeploymentOrchestrator for testing"""
    # This will be used once orchestrator is integrated
    mock = mocker.patch('varitykit.commands.app_deploy.DeploymentOrchestrator')
    mock.return_value.deploy.return_value = {
        'deployment_id': 'deploy-1737492000',
        'frontend_url': 'https://ipfs.io/ipfs/QmTest123',
        'thirdweb_url': 'https://gateway.thirdweb.com/ipfs/QmTest123',
        'cid': 'QmTest123',
        'app_store_url': None
    }
    return mock
