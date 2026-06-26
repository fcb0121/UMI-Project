#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
SESSION_NAME="$(basename "${SESSION_DIR}")"
IMAGE="${KALIBR_DOCKER_IMAGE:-kalibr:ros1-20.04}"

usage() {
  cat <<EOF
Usage: $0 [build|bag|check|camera|calibrate|all|shell] [arguments passed to the command]

Examples:
  $0 build
  $0 bag
  $0 check
  $0 camera --show-extraction
  $0 calibrate
  $0 calibrate --show-extraction
  $0 all --show-extraction
  $0 shell

Environment:
  KALIBR_DOCKER_IMAGE  Docker image name/tag. Default: kalibr:ros1-20.04
  BAG_PATH, TARGET_YAML, CAM_YAML, IMU_YAML, CAM_TOPIC, IMU_TOPIC, CAM_MODELS
EOF
}

command="${1:-calibrate}"
if [[ $# -gt 0 ]]; then
  shift
fi

if [[ "${command}" == "-h" || "${command}" == "--help" || "${command}" == "help" ]]; then
  usage
  exit 0
fi

if [[ "${command}" == "build" ]]; then
  docker build -t "${IMAGE}" -f "${SCRIPT_DIR}/docker/Dockerfile" "${SCRIPT_DIR}/docker"
  exit 0
fi

if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "Docker image '${IMAGE}' was not found."
  echo "Build it first with: ${SCRIPT_DIR}/run_kalibr_docker.sh build"
  exit 1
fi

docker_args=(
  --rm
  --net=host
  --ipc=host
  --user "$(id -u):$(id -g)"
  -e "HOME=/tmp"
  -e "SESSION_NAME=${SESSION_NAME}"
  -e "QT_X11_NO_MITSHM=1"
  -v "${SESSION_DIR}:/data:rw"
)

if [[ -t 0 && -t 1 ]]; then
  docker_args+=(-it)
fi

for env_name in BAG_PATH TARGET_YAML CAM_YAML IMU_YAML CAM_TOPIC IMU_TOPIC CAM_MODELS; do
  if [[ -n "${!env_name:-}" ]]; then
    docker_args+=(-e "${env_name}=${!env_name}")
  fi
done

if [[ -n "${DISPLAY:-}" && -d /tmp/.X11-unix ]]; then
  if command -v xhost >/dev/null 2>&1; then
    xhost +local:root >/dev/null 2>&1 || true
  fi
  docker_args+=(
    -e "DISPLAY=${DISPLAY}"
    -v "/tmp/.X11-unix:/tmp/.X11-unix:rw"
  )
fi

docker run "${docker_args[@]}" "${IMAGE}" \
  /data/kalibr/run_pipeline_in_container.sh "${command}" "$@"
