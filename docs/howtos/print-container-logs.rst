===========================
How to print container logs
===========================

To print the most recent logs for multiple pods and containers, you can use the ``timestamps`` parameter and sort log lines afterwards.
Note that this will not work correctly if your container logs contain newlines!

.. code-block:: python

    tail_lines = 100

    logs = []

    for pod in pods:
        for container in pod.obj["spec"]["containers"]:
            container_log = pod.logs(
                container=container["name"],
                timestamps=True,
                tail_lines=tail_lines,
            )
            for line in container_log.split("\n"):
                logs.append(line)

    logs.sort()

    for log in logs:
        print(log)
