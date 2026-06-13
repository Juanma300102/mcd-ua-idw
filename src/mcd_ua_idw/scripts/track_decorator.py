"""Future DQM execution-tracking decorator.

Tracking writes must use transactions independent from the wrapped script's
transaction so failure records survive a rollback of script work.
"""
