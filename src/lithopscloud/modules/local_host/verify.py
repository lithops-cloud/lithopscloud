from lithopscloud.modules.utils import color_msg, Color


def verify(base_config):
    """:returns a valid localhost configuration, if possible, either as storage or compute backend. """

    if 'localhost' in base_config['lithops']['storage'] and 'localhost' not in base_config['lithops']['backend']:
        print(color_msg("Localhost storage backend cannot be used in serverless mode", Color.RED))  # returns None
    else:  # Localhost is both in storage and compute, or is only compute. Both options are valid.
        return {'lithops': base_config['lithops']}



