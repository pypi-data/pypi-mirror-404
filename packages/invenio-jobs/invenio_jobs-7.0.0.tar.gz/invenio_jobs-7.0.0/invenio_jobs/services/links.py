# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Invenio-Jobs is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Service links."""

from invenio_records_resources.services import EndpointLink


class JobEndpointLink(EndpointLink):
    """Shortcut for writing Run links."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        # Dirty but simpler
        kwargs.setdefault("params", [])
        kwargs["params"].append("job_id")
        super().__init__(*args, **kwargs)

    @staticmethod
    def vars(record, vars):
        """Update vars used to expand the link."""
        vars.update({"job_id": str(record.id)})


class RunEndpointLink(EndpointLink):
    """Shortcut for writing Run links."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        # Dirty but simpler
        kwargs.setdefault("params", [])
        kwargs["params"].extend(["job_id", "run_id"])
        super().__init__(*args, **kwargs)

    @staticmethod
    def vars(record, vars):
        """Update vars used to expand the link."""
        vars.update(
            {
                "job_id": str(record.job_id),
                "run_id": str(record.id),
            }
        )


def vars_func_set_querystring(func_qs=lambda obj, vars: {}):
    """Fill in querystring parameters easily.

    `func_qs` is a function that takes:
    - `obj`: the target object
    - `var`: the dict of values that can be used to expand the endpoint route

    It returns a dict of values that will be merged with the sub-dict at
    vars["args"]. vars["args"] is a special dict whose values will expand
    into querystring parameters when the url is built.

    Overall, the returned function by `vars_func_set_querystring` is meant to
    be passed to an `EndpointLink`'s `vars` parameter.
    """

    def _inner(obj, vars):
        vars.setdefault("args", {})
        vars["args"].update(func_qs(obj, vars))

    return _inner
