"""
Plugin interno: tape (Times & Trades)
"""

def register(cli):
    from .command import tape
    cli.add_command(tape)
