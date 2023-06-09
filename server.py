import sys

from google.cloud import compute_v1
from google.api_core.extended_operation import ExtendedOperation

PROJECT = 'vivid-canyon-389309'
ZONE = 'europe-west1-b'
INSTANCE = 'mc-server'

instances_client = compute_v1.InstancesClient()

def wait_for_extended_operation(operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300):
    result = operation.result(timeout=timeout)

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)
    
    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)
    
    return result

async def start(print_func):
    operation = instances_client.resume(
        project=PROJECT,
        zone=ZONE,
        instance=INSTANCE
    )

    wait_for_extended_operation(operation, "instance start")

    instance = instances_client.get(
        project=PROJECT,
        zone=ZONE,
        instance=INSTANCE
    )

    ip = instance.network_interfaces[0].access_configs[0].nat_i_p

    await print_func(f"`[] Server IP: {ip}`")

async def stop(print_func):
    operation = instances_client.suspend(
        project=PROJECT,
        zone=ZONE,
        instance=INSTANCE
    )

    wait_for_extended_operation(operation, "instance suspension")
