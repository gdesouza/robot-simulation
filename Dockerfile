ARG WEBOTS_IMAGE=cyberbotics/webots:R2025a-ubuntu22.04
FROM ${WEBOTS_IMAGE}
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv xauth \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/robot-venv
COPY requirements-controller.txt /tmp/requirements-controller.txt
RUN /opt/robot-venv/bin/pip install --no-cache-dir -r /tmp/requirements-controller.txt
ENV PATH="/opt/robot-venv/bin:${PATH}" \
    HOME=/tmp/webots-home \
    QT_X11_NO_MITSHM=1 \
    QT_QPA_PLATFORM=xcb \
    LIDAR_HOST=0.0.0.0 \
    LIDAR_PORT=8765
WORKDIR /workspace
COPY . /workspace
COPY docker/entrypoint.sh /usr/local/bin/indoor-webots
RUN chmod 755 /usr/local/bin/indoor-webots
EXPOSE 8765
ENTRYPOINT ["/usr/local/bin/indoor-webots"]
CMD ["gui"]
