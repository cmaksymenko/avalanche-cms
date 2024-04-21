from enum import Enum
from pathlib import Path
import click
from appdirs import user_config_dir
import yaml

class Feature(Enum):
    SHOW_TOKEN = "show-token"
    VERBOSE_ERRORS = "verbose-errors"

class FeatureProperty(Enum):
    EXPOSURE = "exposure"

FEATURE_CONFIG = {
    Feature.SHOW_TOKEN: {FeatureProperty.EXPOSURE: True},
    Feature.VERBOSE_ERRORS: {FeatureProperty.EXPOSURE: False}
}

class FeatureSet(dict):
    
    def __init__(self):
        super().__init__()
        self.config_dir = Path(user_config_dir("cli", "avalanchecms"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "features.yaml"
        self.load_data_from_yaml()
           
    def load_data_from_yaml(self):
        try:
            with open(self.config_file, 'r') as file:
                data = yaml.safe_load(file) or {}
            self.update(data)
        except FileNotFoundError:
            self.save_data_to_yaml()
        except Exception as e:
            click.echo(f"Config load failed.")
            self.backup_and_reset()

    def save_data_to_yaml(self):
        with open(self.config_file, 'w') as file:
            yaml.dump({k: v for k, v in self.items()}, file)
            
    def backup_and_reset(self):
        backup_file = self.config_file.with_suffix('.yaml.bkp')
        if self.config_file.exists():
            self.config_file.rename(backup_file)
            click.echo(f"Backing up to {backup_file}.")
        self.clear()
        click.echo("Config reset.")
        self.save_data_to_yaml()

    def __setitem__(self, key, value):
        if isinstance(key, Enum):
            key = key.name
        super().__setitem__(key, value)
        self.save_data_to_yaml()

    def is_set(self, feature):
        return self.get(feature, False)
    
    def is_set(self, feature):
        feature_key = feature.value if isinstance(feature, Enum) else feature
        return self.get(feature_key, False)

@click.group(name='feature')
def group():
    pass

@group.command('enable')
@click.argument('feature', callback=lambda ctx, param, value: validate_feature(value))
@click.option('-y', '--yes', is_flag=True, help="Skip confirmation.")
def enable_feature(feature, yes=False):
    if FEATURE_CONFIG.get(feature, {}).get(FeatureProperty.EXPOSURE, False):
        if not yes:
            click.echo(f"Warning: {feature.value} may expose sensitive info.")
            if not click.confirm("Continue?"):
                return

    feature_set[feature.value] = True
    click.echo(f"{feature.value} enabled.")

@group.command('disable')
@click.argument('feature', callback=lambda ctx, param, value: validate_feature(value))
def disable_feature(feature):
    feature_set[feature.value] = False
    click.echo(f"{feature.value} disabled.")

def validate_feature(value):
    try:
        if value in Feature._value2member_map_:
            return Feature(value)
        else:
            raise ValueError
    except ValueError:
        raise click.BadParameter(f"'{value} unsupported.")

feature_set = FeatureSet()