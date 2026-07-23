from django.conf import settings


def select_storage(residency=None):
    """
    Return the storage config for a given data-residency (NFR-SEC-3, D-B3).
    Falls back to the 'default' entry for unknown residencies.
    """
    residency = residency or getattr(settings, "DATA_RESIDENCY", "default")
    table = getattr(settings, "DATA_RESIDENCY_STORAGES", {})
    return table.get(residency, table.get("default"))
